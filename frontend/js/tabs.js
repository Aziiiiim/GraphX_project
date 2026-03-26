export function initTabs() {
  const navButtons = document.querySelectorAll(".nav__button");
  const panels = document.querySelectorAll(".panel");

  function showSection(sectionId) {
    navButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.section === sectionId);
    });

    panels.forEach((panel) => {
      panel.classList.toggle("active", panel.id === sectionId);
    });
  }

  navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      showSection(button.dataset.section);
    });
  });
}