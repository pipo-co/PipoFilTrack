function displayTooltip(id) {
  const element = document.getElementById(id);
  if (element.style.visibility == "hidden") {
    element.style.visibility = "visible";
    element.style.opacity = 1;
  }
  else {
    element.style.visibility = "hidden";
    element.style.opacity = 0;
  }
}