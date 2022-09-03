// https://www.freecodecamp.org/news/javascript-debounce-example/
export function debounce(func, timeout = 1000) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

export function download(url, fileName) {
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

export function inRange(value, max, min = 0) {
  return Math.max(Math.min(value, max), min);
}

export function toggleDisabled(elem, cond) {
    if(cond) {
        elem.classList.add('disabled', 'uk-disabled');
    } else {
        elem.classList.remove('disabled', 'uk-disabled');
    }
}
