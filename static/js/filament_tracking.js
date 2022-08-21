"use strict";

// Constants
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#00ff00';
const WEBM_QUALITY      = 1;

const TRACKING_POINT_SIZE           = 5;
const TRACKING_POINT_STATUS_COLOR   = {
    'INTERPOLATED': '#0055ff',
    'PRESERVED':    '#ff0000',
    null:           '#00ff00',
    undefined:      '#00ff00',
}
const TRACKING_POINT_COLOR  = '#0055ff'

const NORMAL_LINE_COLOR     = 'rgba(0,255,255,0.22)'

// Elementos de UI
const selectorCanvas        = document.getElementById('points-selector-canvas');
const selectorWrapper       = document.getElementById('selector-wrapper');
const selectorZone          = document.getElementById('selector-zone');
const previewZone           = document.getElementById('preview-zone');
const previewCanvas         = document.getElementById('preview');
const form                  = document.getElementById('tracking-form');
const imgInput              = document.getElementById('img-input');
const errors                = document.getElementById('errors');
const actionButtons         = document.getElementById('action-buttons');
const pointsButtons         = document.getElementById('point-buttons');
const arrowUpButton         = document.getElementById('arrow-up');
const arrowDownButton       = document.getElementById('arrow-down');
const previewSection        = document.getElementById('preview-section');
const imgButtons            = document.getElementById('img-buttons');
const undo                  = document.getElementById('undo');
const redo                  = document.getElementById('redo');
const resultsViewerUI       = document.getElementById('results-viewer');
const resultsLoader         = document.getElementById('results-loader');
const results               = document.getElementById('results');
const downloadJson          = document.getElementById('download-json');
const downloadWebM          = document.getElementById('download-webm');
const downloadTsv           = document.getElementById('download-tsv');

/* ------ Global data -------- */

// Preview and point selection
const selectedPoints    = [];
const redoPoints        = [];
let selectorDrawable;
let pointSize = POINT_SIZE;
let scale       = 1;
let scaleFactor = 1.1;
let selectorCanvasWidth = 65;

// Results viewer controller
const resultsViewer = new ResultsViewer('result-controls');

(function () {
    form.addEventListener('submit', fullTracking);
    form.addEventListener('input', debouncedPreview);

    imgInput.addEventListener('change', handleImageSelection);

    selectorCanvas.style.display = 'none';
    selectorCanvas.width = CANVAS_RESOLUTION;
    selectorCanvas.addEventListener('click', onCanvasClick);

    // Bind result viewer
    resultsViewer.bindViewer(resultsViewerUI);

    // Undo/Redo selected points
    undo.addEventListener('click', undoPoint);
    redo.addEventListener('click', redoPoint);

    plus.addEventListener('click', addZoom);
    minus.addEventListener('click', reduceZoom);

    arrowUpButton.addEventListener('click', increasePointDiameter);
    arrowDownButton.addEventListener('click', decreasePointDiameter);  
})();

async function fullTracking(e) {
    e.preventDefault();
    clearError();

    const formData = new FormData(form);
    results.hidden = false;
    results.scrollIntoView({behavior: "smooth"});

    try {
        resultsViewerUI.hidden = true;
        resultsLoader.hidden = false;
        const result = await executeTracking(formData);
        await renderTrackingResult(result);
    } catch(error) {
        showError(error);
        results.hidden = true;
        selectorCanvas.scrollIntoView({behavior: "smooth"});
    }
}

function trackingPreview() {
    const formData = new FormData(form);
    
    formData.set('images[]', imgInput.files[0]);

    if(selectedPoints.length >= 2) {
        executeTracking(formData)
            .then(updatePreview)
            .catch(showError)
            ;
    }
}

function debouncedPreview() {
    debounce(trackingPreview)();
}

function debouncedPreview() {
    debounce(trackingPreview)();
}

async function executeTracking(formData) {
    if(selectedPoints.length < 2) {
        return Promise.reject('Debe seleccionar el punto inicial y final del filamento');
    }

    formData.append('points', JSON.stringify(selectedPoints));

    let response;
    try {
        response = await fetch('/track', {method: 'POST', body: formData})
    } catch(error) {
        return Promise.reject('Server Connection Error: ' + error);
    }

    try {
        const body = await response.json();
        if(response.ok) {
            return Promise.resolve(body);
        } else {
            return Promise.reject(body.message);
        }
    } catch(error) {
        return Promise.reject(error);
    }
}

async function resultsToCanvas(trackingResult, drawNormalLines = false, colorSupplier = () => TRACKING_POINT_COLOR) {
    const frames = []

    // We iterate frame results and images at the same time (should have same length)
    const framesIter = drawableIterator(imgInput.files);
    for(const result of trackingResult.frames[Symbol.iterator]()) {
        const {value: frame} = await framesIter.next();
        const canvas = buildCanvas(frame);
        const ctx = canvas.getContext('2d');

        for(const point of result.points) {
            const [x, y] = trackingPoint2canvas(point, canvas, frame);
            drawPoint(ctx, x, y, colorSupplier(point.status), TRACKING_POINT_SIZE);
        }

        if(drawNormalLines) {
            for(const segment of result.metadata.normal_lines) {
                const [x0, y0] = trackingPoint2canvas(segment.start, canvas, frame);
                const [x1, y1] = trackingPoint2canvas(segment.end, canvas, frame);
                drawLine(ctx, x0, y0, x1, y1, NORMAL_LINE_COLOR);
            }
        }

        frames.push(canvas);
        closeFrame(frame);
    }

    return frames
}

async function renderTrackingResult(trackingResult) {
  const frames = await resultsToCanvas(trackingResult);
  resultsLoader.hidden = true;
  resultsViewerUI.hidden = false;

    resultsViewer.loadResults(frames);

    const dateString = new Date().toISOString().split('.')[0].replace(/:/g, '.');
    const resultsFileName = `${imgInput.files[0].name.split('.')[0]}_results_${dateString}`

    if(downloadJson.href) {
        URL.revokeObjectURL(downloadJson.href);
    }
    downloadJson.href       = URL.createObjectURL(new Blob([toJsonResults(trackingResult)], {type: 'application/json'}));
    downloadJson.download   = `${resultsFileName}.json`

    if(downloadTsv.href) {
        URL.revokeObjectURL(downloadTsv.href);
    }
    downloadTsv.href        = URL.createObjectURL(new Blob([toTsvResults(trackingResult)],  {type: 'text/tab-separated-values'}));
    downloadTsv.download    = `${resultsFileName}.tsv`

    downloadWebM.addEventListener('click', () => {
        const vid = new Whammy.Video(resultsViewer.fps, WEBM_QUALITY);
        frames.forEach(frame => vid.add(frame));
        vid.compile(false, video => {
            if(downloadWebM.href) {
                URL.revokeObjectURL(downloadWebM.href);
            }
            download(URL.createObjectURL(video), `${resultsFileName}.webm`);
        });
    });

    resultsViewerUI.style.display = '';
    results.style.display = '';
    results.scrollIntoView({behavior: "smooth"});
}

function download(url, fileName) {
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

async function updatePreview(previewResults) {
    const [frame] = await resultsToCanvas(previewResults, true, (status) => TRACKING_POINT_STATUS_COLOR[status]);
    previewCanvas.classList.remove("loader");
    drawIntoCanvas(previewCanvas, frame);
}

function toJsonResults(results) {
    const redactedResults = results.frames.map(frame => { return {
        points: frame.points.map(point => { return {
            x: point.x,
            y: point.y,
        }}),
    }});
    return JSON.stringify(redactedResults);
}

function toTsvResults(results) {
    const ret = ['frame\tx\ty'];

    let frame = 0;
    for(const result of results.frames) {
        result.points.forEach(point => ret.push([frame, point.x, point.y].join('\t')));
        frame++;
    }

    return ret.join('\r\n');
}

function trackingPoint2canvas({x, y}, canvas, img) {
    return [pixel2CanvasPosX(x, canvas, img), pixel2CanvasPosY(y, canvas, img)];
}

// In case of error returns error message
async function* drawableIterator(images) {
    // Files is not iterable
    for(const image of images) {
        switch(image.type) {
            case 'image/tiff': {
                const buffer = await image.arrayBuffer();
                const ifds = UTIF.decode(buffer);

                for(const ifd of ifds) {
                    UTIF.decodeImage(buffer, ifd, ifds);

                    const rgbaData = UTIF.toRGBA8(ifd);
                    const imageData = new ImageData(new Uint8ClampedArray(rgbaData), ifd.width, ifd.height);

                    const drawable = document.createElement('canvas');
                    drawable.width = ifd.width;
                    drawable.height = ifd.height;

                    // Rendereamos la imagen en un canvas intermedio para luego poder escalar la imagen
                    const ctx = drawable.getContext('2d');
                    ctx.putImageData(imageData, 0, 0, 0, 0, ifd.width, ifd.height);

                    yield drawable;
                }
            } break;
            case 'image/jpeg':
            case 'image/jpg':
            case 'image/png': {
                yield await createImageBitmap(image);
            } break;
            default:
                // Ignoramos tipos que no conocemos
        }
    }
}

function closeFrame(frame) {
    if(frame instanceof ImageBitmap) {
        frame.close()
    }
}

function showError(message) {
    errors.innerText = message;
}

function clearError() {
    errors.innerText = '';
}

function canvasPos2Pixel(pos, canvas_len, img_len) {
    return Math.trunc(pos / canvas_len * img_len)
}
function canvasPos2PixelX(x, canvas_w) {
    return canvasPos2Pixel(x, canvas_w, selectorDrawable.width);
}
function canvasPos2PixelY(y, canvas_h) {
    return canvasPos2Pixel(y, canvas_h, selectorDrawable.height);
}

function pixel2CanvasPos(pixel, canvas_draw_len, img_len) {
    return pixel / img_len * canvas_draw_len;
}
function pixel2CanvasPosX(x, canvas, img) {
    return pixel2CanvasPos(x, canvas.width, img.width);
}
function pixel2CanvasPosY(y, canvas, img) {
    return pixel2CanvasPos(y, canvas.height, img.height);
}

function onCanvasClick(event) {
    const rect = selectorCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const pixel_x = canvasPos2PixelX(x, rect.width);
    const pixel_y = canvasPos2PixelY(y, rect.height);

    // Si agregas un punto, perdes los redo
    redoPoints.length = 0;

    addPointSelection({x: pixel_x, y: pixel_y});
    debouncedPreview()
}

function addPointSelection(point) {
    point.prev = selectedPoints.length > 0
        ? selectedPoints[selectedPoints.length - 1]
        : null
        ;
    selectedPoints.push(point);

    updateInterface();
    drawPointSelection(point);
}

function drawPointSelection(point) {
    const ctx = selectorCanvas.getContext("2d");

    // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
    const x = pixel2CanvasPosX(point.x + 0.5, selectorCanvas, selectorDrawable);
    const y = pixel2CanvasPosY(point.y + 0.5, selectorCanvas, selectorDrawable);

    // Line
    if(point.prev) {
        const prev = point.prev;
        const prevX = pixel2CanvasPosX(prev.x + 0.5, selectorCanvas, selectorDrawable);
        const prevY = pixel2CanvasPosY(prev.y + 0.5, selectorCanvas, selectorDrawable);
        drawLine(ctx, prevX, prevY, x, y, POINT_COLOR)
    }

    drawPoint(ctx, x, y, POINT_COLOR, pointSize);
}

function undoPoint() {
    const ctx = selectorCanvas.getContext("2d");

    if(selectedPoints.length > 0) {
        redoPoints.push(selectedPoints.pop());

        // Clean canvas
        ctx.clearRect(0, 0, selectorCanvas.width, selectorCanvas.height);

        // Redraw image
        canvasDisableSmoothing(ctx);
        ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

        // Redraw all poins
        selectedPoints.forEach(drawPointSelection)
        updateInterface();
    }
    debouncedPreview()
}

function redoPoint() {
    if(redoPoints.length > 0) {
        const point = redoPoints.pop();
        addPointSelection(point)
    }
    debouncedPreview()
}

function rcLoop() {
    result_viewer.loop = !result_viewer.loop
}

function rcFrameRateChange(delta) {
    result_viewer.fps.value += delta;
    if(result_viewer.fps.value <= 0) {
        result_viewer.fps.value = 1;
    }
    result_viewer.fps.update();
    restartResultsAnimation();
}

function addZoom() {
  if (selectorCanvasWidth > 100) {
    //si pase los 100, tengo que darle toda la pantalla, para eso se desplaza abajo
    // la seccion de preview y de parametros
    selectorZone.classList.remove("uk-width-3-5")
    selectorZone.classList.add("uk-width-1-1")
    previewZone.classList.add("uk-flex-last")
    previewZone.classList.remove("uk-width-2-5")
    previewZone.classList.add("uk-width-1-1")
  }
  selectorCanvasWidth = selectorCanvasWidth * scaleFactor
  selectorCanvas.style.width = selectorCanvasWidth + "vh" 
}

function reduceZoom() {
  if (selectorCanvasWidth <= 100) {
    selectorZone.classList.remove("uk-width-1-1")
    selectorZone.classList.add("uk-width-3-5")
    previewZone.classList.remove("uk-flex-last")
    previewZone.classList.remove("uk-width-1-1")
    previewZone.classList.add("uk-width-2-5")
  }
  selectorCanvasWidth = selectorCanvasWidth * (1/scaleFactor)
  selectorCanvas.style.width = selectorCanvasWidth + "vh"
}

function increasePointDiameter() {
  pointSize = pointSize + 1
}

function decreasePointDiameter() {
  if (pointSize > 1) pointSize = pointSize - 1;
}

function updateInterface() {
    actionButtons.hidden = selectedPoints.length === 0 && redoPoints.length === 0 ? true : false  
    pointsButtons.hidden = selectedPoints.length === 0 && redoPoints.length === 0 ? true : false 
    previewSection.hidden = selectedPoints.length < 2 ? true : false  
    undo.style.visibility = selectedPoints.length === 0 ? 'hidden' : 'visible';
    redo.style.visibility = redoPoints.length === 0 ? 'hidden' : 'visible';
    clearError();
}

// Empty selected points and build canvas for point selection
async function handleImageSelection() {
    if(imgInput.files.length === 0) {
          // No nos subieron nada
          showError('No images selected');
          imgInput.value = '';
          return;
    }
    imgButtons.hidden = false;
    const firstDrawable = await drawableIterator(imgInput.files).next();
    if(!firstDrawable || firstDrawable.done) {
        showError('No valid image selected');
        imgInput.value = '';
        return;
    }

    // Get selector drawable value
    if(selectorDrawable) {
        closeFrame(selectorDrawable);
    }
    selectorDrawable = firstDrawable.value;

    // Update selector canvas with new drawable
    selectorCanvas.height = selectorCanvas.width / selectorDrawable.width * selectorDrawable.height;
    const ctx = selectorCanvas.getContext('2d');
    canvasDisableSmoothing(ctx);
    ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

    // Show canvas
    selectorWrapper.hidden = false;
    selectorCanvas.style.display = '';
    pointsButtons.hidden = false;

    // Reset selected points
    selectedPoints.length    = 0;
    redoPoints.length        = 0;
}
