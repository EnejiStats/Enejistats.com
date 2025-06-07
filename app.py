from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Club, PlayerProfile, PlayerMatchStat, Match, ScoutProfile, PlayerClubHistory, ScoutingReport, RoleEnum
from forms import LoginForm, PlayerRegistrationForm, ClubRegistrationForm, ScoutRegistrationForm, ScoutingReportForm, PlayerClubHistoryForm
from datetime import datetime
import os

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object('config.DevConfig' if env == 'development' else 'config.ProdConfig')

    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('landing.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
            flash('Invalid credentials', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/register/player', methods=['GET', 'POST'])
    def register_player():
        form = PlayerRegistrationForm()
        form.club_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Club.query.order_by(Club.name)]
        if form.validate_on_submit():
            new_player = PlayerProfile(
                first_name=form.first_name.data,
                middle_name=form.middle_name.data,
                last_name=form.last_name.data,
                dob=form.dob.data,
                nationality=form.nationality.data,
                gender=form.gender.data,
                dominant_foot=form.dominant_foot.data,
                weak_foot_pct=form.weak_foot_pct.data,
                height_cm=form.height_cm.data,
                weight_kg=form.weight_kg.data,
                club_id=form.club_id.data or None
            )
            db.session.add(new_player)
            db.session.commit()
            flash('Player registered!', 'success')
            return redirect(url_for('index'))
        return render_template('register_player.html', form=form)

    @app.route('/players')
    def players():
        q = request.args.get('q', '')
        nat = request.args.get('nationality', '')
        players = PlayerProfile.query
        if q:
            players = players.filter(PlayerProfile.last_name.ilike(f"%{q}%"))
        if nat:
            players = players.filter_by(nationality=nat)
        players = players.all()
        return render_template('players.html', players=players)

    @app.route('/players/<int:pid>')
    def player_detail(pid):
        player = PlayerProfile.query.get_or_404(pid)
        summary = db.session.query(
            db.func.sum(PlayerMatchStat.minutes).label('minutes'),
            db.func.avg(PlayerMatchStat.short_pass_succ + PlayerMatchStat.long_pass_succ).label('avg_pass_succ')
        ).filter_by(player_id=pid).first()

        history = PlayerClubHistory.query.filter_by(player_id=pid).join(Club).order_by(PlayerClubHistory.start_date.desc()).all()
        reports = ScoutingReport.query.filter_by(player_id=pid).join(ScoutProfile).order_by(ScoutingReport.date_created.desc()).all()

        return render_template('player_detail.html', player=player, summary=summary, history=history, reports=reports)

    @app.route('/scout/report', methods=['GET', 'POST'])
    @login_required
    def scout_report():
        if current_user.role != RoleEnum.SCOUT:
            flash('Access denied: Only scouts may submit reports.', 'danger')
            return redirect(url_for('index'))

        form = ScoutingReportForm()
        form.player_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in PlayerProfile.query.order_by(PlayerProfile.last_name)]

        if form.validate_on_submit():
            scout = ScoutProfile.query.filter_by(user_id=current_user.id).first()
            if not scout:
                flash('Scout profile not found.', 'danger')
                return redirect(url_for('index'))

            report = ScoutingReport(
                player_id=form.player_id.data,
                scout_id=scout.id,
                notes=form.notes.data,
                rating=form.rating.data,
                date_created=datetime.utcnow()
            )
            db.session.add(report)
            db.session.commit()
            flash('Scouting report submitted.', 'success')
            return redirect(url_for('players'))

        return render_template('scout_report.html', form=form)

    @app.route('/players/history', methods=['GET', 'POST'])
    @login_required
    def player_club_history():
        if current_user.role not in [RoleEnum.CTO, RoleEnum.ADMIN]:
            flash('Access denied: Admins only.', 'danger')
            return redirect(url_for('index'))

        form = PlayerClubHistoryForm()
        form.player_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in PlayerProfile.query.order_by(PlayerProfile.last_name)]
        form.club_id.choices = [(c.id, c.name) for c in Club.query.order_by(Club.name)]

        if form.validate_on_submit():
            history = PlayerClubHistory(
                player_id=form.player_id.data,
                club_id=form.club_id.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data
            )
            db.session.add(history)
            db.session.commit()
            flash('Club history recorded.', 'success')
            return redirect(url_for('players'))

        return render_template('player_club_history.html', form=form)

    @app.route('/api/v1/player_stats', methods=['POST'])
    @login_required
    def api_player_stats():
        if current_user.role not in [RoleEnum.CTO, RoleEnum.ADMIN, RoleEnum.SCOUT]:
            return jsonify({'error': 'unauthorized'}), 403
        data = request.get_json()
        pstat = PlayerMatchStat(**data)
        db.session.add(pstat)
        db.session.commit()
        return jsonify({'status': 'ok'}), 201

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
