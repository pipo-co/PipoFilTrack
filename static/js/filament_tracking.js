"use strict";


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
const selectorWrapper       = document.getElementById('selector-wrapper');
const selectorZone          = document.getElementById('selector-zone');
const previewZone           = document.getElementById('preview-zone');
const previewCanvas         = document.getElementById('preview');
const trackingForm          = document.getElementById('tracking-form');
const imgInput              = document.getElementById('img-input');
const errors                = document.getElementById('errors');
const actionButtons         = document.getElementById('action-buttons');
const arrowUpButton         = document.getElementById('arrow-up');
const arrowDownButton       = document.getElementById('arrow-down');
const trackButtonContainer  = document.getElementById('track-button');
const undo                  = document.getElementById('undo');
const redo                  = document.getElementById('redo');
const resultsViewerUI       = document.getElementById('results-viewer');
const resultsContainer      = document.getElementById('results-container');
const resultsLoader         = document.getElementById('results-loader');
const results               = document.getElementById('results');
const downloadJson          = document.getElementById('download-json');
const downloadWebM          = document.getElementById('download-webm');
const downloadTsv           = document.getElementById('download-tsv');
const rvRenderingProps      = document.getElementById('rv-rendering-properties');

/* ------ Global data -------- */

// Preview and point selection
let selectorDrawable;
let pointSize = POINT_SIZE;
let scale       = 1;
let scaleFactor = 1.1;
let selectorCanvasWidth = 65;
let currentResults;

// Results viewer controller
const resultsViewer = new ResultsViewer('result-controls');
const pointSelector = new PointsSelector(debouncedPreview, 'point-selector-controls-template');

(function () {
    trackingForm.addEventListener('submit', fullTracking);
    trackingForm.addEventListener('input', debouncedPreview);

    imgInput.addEventListener('change', handleImageSelection);

    // Bind result viewer
    resultsViewer.bind(resultsViewerUI);
    pointSelector.bind(selectorWrapper);

    // // Undo/Redo selected points
    // undo.addEventListener('click', undoPoint);
    // redo.addEventListener('click', redoPoint);

    // plus.addEventListener('click', addZoom);
    // minus.addEventListener('click', reduceZoom); 

    // arrowUpButton.addEventListener('click', increasePointDiameter);
    // arrowDownButton.addEventListener('click', decreasePointDiameter); 
})();


async function fullTracking(e) {
    e.preventDefault();
    clearError();

    const formData = new FormData(trackingForm);
    results.hidden = false;
    results.scrollIntoView({behavior: "smooth"});

    try {
        resultsContainer.hidden = true;
        resultsLoader.hidden = false;
        console.log('Calling executeTracking');
        currentResults = await executeTracking(formData);
        console.log('Calling processTrackingresults');
        await processTrackingresults(currentResults);
    } catch(error) {
        showError(error);
        results.hidden = true;
    }
}

function togglePreview() {
    preview.hidden = pointSelector.selectedPoints.length < 2 ? true : false;
}

function trackingPreview() {
    const formData = new FormData(trackingForm);
    
    formData.set('images[]', imgInput.files[0]);

    if(pointSelector.selectedPoints.length >= 2) {
        togglePreview();
        executeTracking(formData)
            .then(updatePreview)
            .catch(showError)
            ;
    }
}

function debouncedPreview() {
    debounce(trackingPreview)();
}

async function executeTracking(formData) {
    if(pointSelector.selectedPoints.length < 2) {
        return Promise.reject('Debe seleccionar el punto inicial y final del filamento');
    }

    formData.append('points', JSON.stringify(pointSelector.selectedPoints));

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

async function resultsToCanvas(trackingResult, renderParams) {
    const frames = []

    // We iterate frame results and images at the same time (should have same length)
    const framesIter = drawableIterator(imgInput.files);
    for(const result of trackingResult.frames[Symbol.iterator]()) {
        const {value: frame} = await framesIter.next();
        const canvas = buildCanvas(frame);
        const ctx = canvas.getContext('2d');

        for(const point of result.points) {
            const [x, y] = trackingPoint2canvas(point, canvas, frame);
            drawPoint(ctx, x, y, renderParams.colorSupplier(point.status), TRACKING_POINT_SIZE);
        }

        if(renderParams.normalLines) {
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

async function processTrackingresults(trackingResult) {
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

    rvRenderingProps.addEventListener('input', () => renderTrackingResult(trackingResult));

    console.log('Calling renderTrackingResult');
    await renderTrackingResult(trackingResult);
    
    resultsViewerUI.classList.remove("loader");
    resultsLoader.hidden = true;
    resultsContainer.hidden = false;
    
    resultsViewerUI.style.display = '';
    results.style.display = '';
    results.scrollIntoView({behavior: "smooth"});
}

async function renderTrackingResult(trackingResult) {
    const frames = await resultsToCanvas(trackingResult, formToRenderParams(rvRenderingProps));
    resultsViewer.loadResults(frames);

    downloadWebM.addEventListener('click', () => {
        const vid = new Whammy.Video(resultsViewer.fps, WEBM_QUALITY);
        UIkit.notification('Download started');
        frames.forEach(frame => vid.add(frame));
        vid.compile(false, video => {
            if(downloadWebM.href) {
                URL.revokeObjectURL(downloadWebM.href);
            }
            download(URL.createObjectURL(video), `${resultsFileName}.webm`);
        });
    });
}


async function updatePreview(previewResults) {
    const [frame] = await resultsToCanvas(previewResults, new RenderParams({normalLines: true, colorCoding: true}));
    previewCanvas.classList.remove("loader");
    drawIntoCanvas(previewCanvas, frame);
}

function toJsonResults(resultData) {
    const redactedResults = resultData.frames.map(frame => { return {
        points: frame.points.map(point => { return {
            x: point.x,
            y: point.y,
        }}),
    }});
    return JSON.stringify(redactedResults);
}

function toTsvResults(resultData) {
    const ret = ['frame\tx\ty'];

    let frame = 0;
    for(const result of resultData.frames) {
        result.points.forEach(point => ret.push([frame, point.x, point.y].join('\t')));
        frame++;
    }

    return ret.join('\r\n');
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

// Empty selected points and build canvas for point selection
async function handleImageSelection() {
    if(imgInput.files.length === 0) {
          // No nos subieron nada
          showError('No images selected');
          imgInput.value = '';
          return;
    }
    trackButtonContainer.hidden = false;
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

    pointSelector.loadImage(selectorDrawable);

    // Show canvas
    selectorWrapper.hidden = false;

    // Reset selected points
    pointSelector.selectedPoints.length    = 0;
    pointSelector.redoPoints.length        = 0;
}

function formToRenderParams(form) {
    return new RenderParams({
        normalLines: form['normal-lines'].checked, 
        colorCoding: form['color-coding'].checked
    });
}

class RenderParams {
    constructor({normalLines, colorCoding}) {
        this.normalLines = normalLines;
        
        if(colorCoding) {
            this.colorSupplier = (status) => TRACKING_POINT_STATUS_COLOR[status];
        } else {
            this.colorSupplier = () => TRACKING_POINT_COLOR;
        }
    }
}