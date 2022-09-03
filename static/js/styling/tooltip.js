function displayTooltip(id) {
  debugger;
  const element = document.getElementById(id);
  if (element.hidden) {
    element.hidden = false;
    element.style.opacity = "1";
  }
  else {
    element.hidden = true;
    element.style.opacity = "0";
  }
}