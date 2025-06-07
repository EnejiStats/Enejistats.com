document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector("input[name='q']");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      document.querySelector("form").submit();
    });
  }
});
