import {JSZip} from "./libs/jszip.min.js";

import ResultsViewer from "./controllers/results.js";
import PointsSelector from "./controllers/selector.js";

import {debounce, download} from "./utils/misc.js";
import {buildImageCanvas, drawIntoCanvasZoomed, drawLine, drawPoint, trackingPoint2canvas} from "./utils/canvas.js";
import {closeImage, fileIterator, imageIterator} from "./utils/images.js";

/* --------- Constants ------------ */
// Horizontal resolution in pixels of all canvas used. Height is calculated to maintain aspect ratio of images.
const CANVAS_RESOLUTION = 1080;

// Format of the zipped result images
const RESULTS_FORMAT = 'png';

// Color and sizes of graphic elements used to render tracking results.
const TRACKING_POINT_SIZE           = 5;
const TRACKING_NORMAL_LINE_WIDTH    = 5;
const TRACKING_POINT_STATUS_COLOR   = {
    'INTERPOLATED': '#0055ff',
    'PRESERVED':    '#ff0000',
    null:           '#00ff00',
    undefined:      '#00ff00',
}
const TRACKING_NORMAL_LINE_COLOR = 'rgba(0,255,255,0.22)'

// Color and sizes of graphic elements used make initial point selection.
const SELECTION_POINT_SIZE  = 10;
const SELECTION_LINE_WIDTH  = 5;
const SELECTION_COLOR       = '#00ff00';

/* -------- UI Elements -------- */
const selectorWrapper       = document.getElementById('selector-wrapper');
const previewCanvas         = document.getElementById('preview');
const trackingForm          = document.getElementById('tracking-form');
const imgInput              = document.getElementById('img-input');
const errors                = document.getElementById('errors');
const trackButtonContainer  = document.getElementById('track-button');
const resultsViewerUI       = document.getElementById('results-viewer');
const resultsContainer      = document.getElementById('results-container');
const previewLoader         = document.getElementById('preview-loader');
const resultsLoader         = document.getElementById('results-loader');
const results               = document.getElementById('results');
const downloadJson          = document.getElementById('download-json');
const downloadZip           = document.getElementById('download-zip');
const downloadTsv           = document.getElementById('download-tsv');
const rvRenderingProps      = document.getElementById('rv-rendering-properties');

/* -------- Global variable -------- */
const debouncedPreviewHandler = debounce(trackingPreview);
let downloadZipEventHandler
let resultViewerPropertiesHandler
let previewFrame

/* -------- Controllers -------- */
const resultsViewer = new ResultsViewer('result-controls');
const pointSelector = new PointsSelector('point-selector', SELECTION_POINT_SIZE, SELECTION_LINE_WIDTH, SELECTION_COLOR, debouncedPreviewHandler, onZoomUpdate);

/* -------- Main -------- */
;(function () {
    trackingForm.addEventListener('submit', fullTracking);
    trackingForm.addEventListener('input', debouncedPreviewHandler);

    imgInput.addEventListener('change', handleImageSelection);

    previewCanvas.width = CANVAS_RESOLUTION;

    // Bind controllers
    resultsViewer.bind(resultsViewerUI, CANVAS_RESOLUTION);
    pointSelector.bind(selectorWrapper, CANVAS_RESOLUTION);
})();

/* -------- Image Selection -------- */
// Empty selected points and build canvas for point selection
async function handleImageSelection() {
    if(imgInput.files.length === 0) {
          // No nos subieron nada
          showError('No images selected');
          imgInput.value = '';
          return;
    }

    // Show track button
    trackButtonContainer.hidden = false;

    const firstFrame = await imageIterator(imgInput.files).next();
    if(!firstFrame || firstFrame.done) {
        showError('No valid image selected');
        imgInput.value = '';
        return;
    }

    // Set selector image value
    if(pointSelector.image) {
        closeImage(pointSelector.image);
    }
    pointSelector.loadImage(firstFrame.value.data);

    // Show canvas
    selectorWrapper.hidden = false;

    // Reset selected points
    pointSelector.selectedPoints.length    = 0;
    pointSelector.redoPoints.length        = 0;
}

/* -------- Tracking -------- */
async function fullTracking(e) {
    e.preventDefault();
    clearError();

    results.hidden = false;
    results.scrollIntoView({behavior: "smooth"});

    try {
        resultsContainer.hidden = true;
        resultsLoader.hidden = false;

        const currentResults = await executeTracking(new FormData(trackingForm));
        await processTrackingResults(currentResults);
    } catch(error) {
        showError(error);
        results.hidden = true;
    }
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
        return Promise.reject(`Server Connection Error: ${error}`);
    }

    try {
        const body = await response.json();
        if(response.ok) {   
            return Promise.resolve(body);
        }
        // Error del back
        return Promise.reject(body.message);
    } catch(error) {
        if(!response.ok) {
            // Error en nginx => HTML => no es json
            return Promise.reject(`Server Error: ${response.status} - ${response.statusText}`);
        }
        // Error en json
        return Promise.reject('Error procesando la respuesta.');
    }
}

/* -------- Preview -------- */
async function trackingPreview() {
    clearError();

    if(pointSelector.selectedPoints.length < 2) {
      previewCanvas.style.visibility = 'hidden';
      previewLoader.hidden = true;
      return;
    }

    const formData = new FormData(trackingForm);
    const {value: previewFile} = await fileIterator(imgInput.files).next();
    formData.set('images[]', previewFile);

    previewLoader.hidden = false;
    previewCanvas.style.visibility = 'hidden';
    executeTracking(formData)
        .then(updatePreview)
        .catch(showError)
        ;
}

async function updatePreview(previewResults) {
  if(previewResults.errors && previewResults.errors.length > 0) {
      showTrackingErrors(previewResults.errors);
  }

  const [{data: frame}] = await resultsToCanvas(previewResults, new RenderParams({normalLines: true, colorCoding: true}), CANVAS_RESOLUTION);
  previewLoader.hidden = true;
  previewCanvas.hidden = false;
  previewCanvas.style.visibility = 'visible';
  previewFrame = frame;
  drawIntoCanvasZoomed(previewCanvas, previewFrame, pointSelector.imgOffset, pointSelector.zoomFactor, pointSelector.image.width, pointSelector.image.height);
}

async function onZoomUpdate() {
    if(previewFrame) {
        drawIntoCanvasZoomed(previewCanvas, previewFrame, pointSelector.imgOffset, pointSelector.zoomFactor, pointSelector.image.width, pointSelector.image.height);
    }
}

/* -------- Results -------- */
async function processTrackingResults(trackingResult) {
    if(trackingResult.errors && trackingResult.errors.length > 0) {
        showTrackingErrors(trackingResult.errors);
    }

    const dateString = new Date().toISOString().split('.')[0].replace(/:/g, '.');
    const resultsFileName = `${imgInput.files[0].name.substring(0, imgInput.files[0].name.lastIndexOf('.'))}_results_${dateString}`

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

    if(resultViewerPropertiesHandler) {
        rvRenderingProps.removeEventListener('input', resultViewerPropertiesHandler);
    }
    resultViewerPropertiesHandler = () => renderTrackingResult(trackingResult, resultsFileName);
    rvRenderingProps.addEventListener('input', resultViewerPropertiesHandler);

    await renderTrackingResult(trackingResult, resultsFileName);

    resultsLoader.hidden = true;
    resultsContainer.hidden = false;

    results.hidden = false;
    results.scrollIntoView({behavior: "smooth"});
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

async function renderTrackingResult(trackingResult, resultsFileName) {
    const frames = await resultsToCanvas(trackingResult, RenderParams.fromForm(rvRenderingProps));
    resultsViewer.loadResults(frames.map(f => f.data));

    if(downloadZipEventHandler) {
        downloadZip.removeEventListener('click', downloadZipEventHandler);
    }
    downloadZipEventHandler = async () => {
        const zip = new JSZip();
        UIkit.notification('Download started');

        for(const frame of frames) {
            const blob = await new Promise(resolve => frame.data.toBlob(resolve));
            const name = frame.name.substring(0, frame.name.lastIndexOf('.'));
            zip.file(`${name}.${RESULTS_FORMAT}`, blob)
          }

        zip .generateAsync({type:"blob"})
            .then(content => download(URL.createObjectURL(content), `${resultsFileName}.zip`))
            ;
    };
    downloadZip.addEventListener('click', downloadZipEventHandler);
}

async function resultsToCanvas(trackingResult, renderParams, canvasResolution = CANVAS_RESOLUTION) {
    const frames = []
    // We iterate frame results and images at the same time (should have same length)
    const framesIter = imageIterator(imgInput.files);
    for(const result of trackingResult.frames[Symbol.iterator]()) {
        const {value: {data: frame, name: imgName}} = await framesIter.next();

        const canvas = buildImageCanvas(frame, canvasResolution);
        const ctx = canvas.getContext('2d');

        for(const point of result.points) {
            const [x, y] = trackingPoint2canvas(point, canvas, frame);
            drawPoint(ctx, x, y, renderParams.colorSupplier(point.status), TRACKING_POINT_SIZE);
        }

        if(renderParams.normalLines) {
            for(const segment of result.metadata.normal_lines) {
                const [x0, y0] = trackingPoint2canvas(segment.start, canvas, frame);
                const [x1, y1] = trackingPoint2canvas(segment.end, canvas, frame);
                drawLine(ctx, x0, y0, x1, y1, TRACKING_NORMAL_LINE_COLOR, TRACKING_NORMAL_LINE_WIDTH);
            }
        }

        frames.push({data: canvas, name: imgName});
        closeImage(frame);
    }

    return frames
}

class RenderParams {
    constructor({normalLines, colorCoding}) {
        this.normalLines = normalLines;
        
        if(colorCoding) {
            this.colorSupplier = (status) => TRACKING_POINT_STATUS_COLOR[status];
        } else {
            this.colorSupplier = () => TRACKING_POINT_STATUS_COLOR[null];
        }
    }

    static fromForm(form) {
        return new RenderParams({
            normalLines: form['normal-lines'].checked,
            colorCoding: form['color-coding'].checked
        });
    }
}

/* ------------ Errors ----------- */
function showTrackingErrors(errors) {
    showError('Tracking errors:\n\t- ' + errors.join('\n\t- '));
}

function showError(message) {
    errors.innerText = message;
}

function clearError() {
    errors.innerText = '';
}
