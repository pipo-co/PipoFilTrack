import {
    canvasDisableSmoothing,
    canvasPos2Pixel,
    drawLine,
    drawPoint,
    pixel2CanvasPos,
    resizeCanvasHeight
} from "../utils/canvas.js";
import {inRange, toggleDisabled} from "../utils/misc.js";

// Constants
const ZOOM_FACTOR = 2;

export default class PointsSelector {
    constructor(templateId, pointSize, lineWidth, color, onSelectionCallback) {
        // Params
        this.templateId         = templateId;
        this.pointSize          = pointSize;
        this.lineWidth          = lineWidth;
        this.color              = color;
        this.onSelectionCallback= onSelectionCallback;
        // UI Bindings
        this.bindPoint          = null;
        this.controls           = null;
        this.canvas             = null;
        // Selection image and points
        this.image              = null;
        this.selectedPoints     = [];
        this.redoPoints         = [];
        // Zoom
        this.mode               = 'draw';
        this.imgOffset          = { x: 0, y: 0 };
        this.zoomFactor         = 1;
        this.savedMov           = { x: 0, y: 0 };

        this.moveHandler = e => this.moveSelection(e);
    }

    bind(bindElement, canvasWidth) {
        this.bindPoint = bindElement;
        bindElement.hidden = true;

        const template = document.getElementById(this.templateId);
        bindElement.appendChild(template.content.cloneNode(true));

        this.canvas = document.getElementById('ps-canvas');
        this.canvas.width = canvasWidth;
        this.canvas.addEventListener('click',       event => this.onCanvasClick(event));
        this.canvas.addEventListener('mousedown',   event => this.startMove(event));

        this.controls = {
            controls:       document.getElementById('ps-controls'),
            zoomIn:         document.getElementById('ps-zoom-in'),
            zoomOut:        document.getElementById('ps-zoom-out'),
            zoom:           document.getElementById('ps-zoom-value'),
            draw:           document.getElementById('ps-draw'),
            move:           document.getElementById('ps-move'),
        };

        this.controls.zoomIn        .addEventListener('click', () => this.updateZoom(ZOOM_FACTOR));
        this.controls.zoomOut       .addEventListener('click', () => this.updateZoom(1/ZOOM_FACTOR));
        this.controls.draw          .addEventListener('click', () => this.updateMode('draw'));
        this.controls.move          .addEventListener('click', () => this.updateMode('move'));

        // Initialize UI elements
        this.updateMode(this.mode);
        this.onZoomUpdate();
    }

    updateMode(newMode) {
        this.canvas.classList.remove(this.mode);
        this.canvas.classList.add(newMode);

        this.controls[this.mode].classList.remove('toggled-button');
        this.controls[newMode].classList.add('toggled-button');

        this.mode = newMode;
    }

    loadImage(image) {
        this.bindPoint.hidden = false;
        this.image = image;
        resizeCanvasHeight(this.canvas, this.image.width, this.image.height);

        this.resetZoom();
        this.drawImage();
        this.updateMode('draw');
        this.controls.controls.hidden = false;
    }

    updateZoom(factor) {
        this.zoomFactor = Math.max(this.zoomFactor * factor, 1);
        this.redraw();
        this.onZoomUpdate();
    }

    resetZoom() {
        this.imgOffset  = { x: 0, y: 0};
        this.zoomFactor = 1;
        this.savedMov   = { x: 0, y: 0 };
        this.onZoomUpdate();
    }

    startMove(event) {
        if(this.mode === 'move' && event.button === 0) {
            this.canvas.addEventListener('mousemove', this.moveHandler);
            document.body.addEventListener('mouseup', e => {
                if(e.button === 0) {
                    this.canvas.removeEventListener('mousemove', this.moveHandler);
                }
            });
        }
    }

    ensureBounds() {
        this.imgOffset.x = inRange(this.imgOffset.x, this.image.width - this.sourceWidth);
        this.imgOffset.y = inRange(this.imgOffset.y, this.image.height - this.sourceHeight);

    }

    moveSelection(event) {
        const rect = this.canvas.getBoundingClientRect();

        const movX = canvasPos2Pixel(event.movementX + this.savedMov.x, rect.width, this.sourceWidth);
        const movY = canvasPos2Pixel(event.movementY + this.savedMov.y, rect.width, this.sourceHeight);

        this.imgOffset.x -= movX;
        this.imgOffset.y -= movY;

        this.savedMov = {
            x: movX === 0 ? this.savedMov.x + event.movementX : 0,
            y: movY === 0 ? this.savedMov.y + event.movementY : 0,
        }

        if(movX !== 0 || movY !== 0) {
            this.redraw();
        }
    }

    redraw() {
        this.ensureBounds();
        this.drawImage();
        this.drawAllPoints();
    }

    updateZoomValueDisplay() {
        this.controls.zoom.innerText = `${this.zoomFactor * 100}%`
    }

    get sourceHeight() {
        return Math.trunc(this.image.height / this.zoomFactor);
    }
    get sourceWidth() {
        return Math.trunc(this.image.width / this.zoomFactor);
    }

    drawImage() {
        const ctx = this.canvas.getContext('2d');
        canvasDisableSmoothing(ctx);
        ctx.drawImage(this.image, this.imgOffset.x, this.imgOffset.y, this.sourceWidth, this.sourceHeight, 0, 0, this.canvas.width, this.canvas.height);
    }

    drawAllPoints() {
        this.selectedPoints.forEach(point => this.drawPointSelection(point));
    }

    onCanvasClick(event) {
        if(this.mode !== 'draw') {
            return;
        }

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const pixel_x = canvasPos2Pixel(x, rect.width, this.sourceWidth, this.imgOffset.x);
        const pixel_y = canvasPos2Pixel(y, rect.height, this.sourceHeight, this.imgOffset.y);
        // Si agregas un punto, perdes los redo
        this.redoPoints.length = 0;

        this.addPointSelection({ x: pixel_x, y: pixel_y });
        this.onSelectionCallback();
    }

    addPointSelection(point) {
        point.prev = this.selectedPoints.length > 0
            ? this.selectedPoints[this.selectedPoints.length - 1]
            : null
            ;
        this.selectedPoints.push(point);

        this.drawPointSelection(point);
    }

    drawPointSelection(point) {
        const ctx = this.canvas.getContext("2d");

        // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
        const x = pixel2CanvasPos(point.x + 0.5, this.canvas.width, this.sourceWidth, this.imgOffset.x);
        const y = pixel2CanvasPos(point.y + 0.5, this.canvas.height, this.sourceHeight, this.imgOffset.y);

        // Line
        if(point.prev) {
            const prev = point.prev;
            const prevX = pixel2CanvasPos(prev.x + 0.5, this.canvas.width, this.sourceWidth, this.imgOffset.x);
            const prevY = pixel2CanvasPos(prev.y + 0.5, this.canvas.height, this.sourceHeight, this.imgOffset.y);
            drawLine(ctx, prevX, prevY, x, y, this.color, this.lineWidth);
        }

        drawPoint(ctx, x, y, this.color, this.pointSize);
    }

    undoPoint() {
        const ctx = this.canvas.getContext("2d");

        if (selectedPoints.length > 0) {
            redoPoints.push(selectedPoints.pop());

            // Clean canvas
            ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // Redraw image
            canvasDisableSmoothing(ctx);
            ctx.drawImage(this.image, 0, 0, this.canvas.width, this.canvas.height);

            // Redraw all poins
            updateInterface();
        }
        this.onSelectionCallback()
    }

    redoPoint() {
        if (redoPoints.length > 0) {
            const point = redoPoints.pop();
            addPointSelection(point)
        }
        this.onSelectionCallback()
    }

    increasePointDiameter() {
        pointSize = pointSize + 1
    }

    decreasePointDiameter() {
        if (pointSize > 1) pointSize = pointSize - 1;
    }

    updateInterface() {
        actionButtons.hidden = selectedPoints.length === 0 && redoPoints.length === 0 ? true : false
        pointsButtons.hidden = selectedPoints.length === 0 && redoPoints.length === 0 ? true : false
        previewPlaceholder.hidden = selectedPoints.length < 2 ? true : false
        undo.style.visibility = selectedPoints.length === 0 ? 'hidden' : 'visible';
        redo.style.visibility = redoPoints.length === 0 ? 'hidden' : 'visible';
        clearError();
    }

    onZoomUpdate() {
        const cond = this.zoomFactor === 1;
        toggleDisabled(this.controls.move, this.zoomFactor === 1);
        if(cond && this.mode === 'move') {
            this.updateMode('draw');
        }

        this.updateZoomValueDisplay();
    }
}
