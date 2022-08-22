// Constants
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#00ff00';

class PointsSelector {
    constructor(onClickCallback, templateId) {
        this.templateId = templateId;
        this.onClickCallback = onClickCallback
        this.image = null;
        this.selectedPoints = [];
        this.redoPoints = [];
        this.moveListener = null;
        this.drawing = true;
        this.imgOffset = { x: 0, y: 0 };
        this.zoomFactor = 1;
        this.controls = null;
        this.bindPoint = null;
        this.canvas = null;    

        this.moveHandler = e => this.moveSelection(e);
    }

    bind(bindElement) {
        this.bindPoint = bindElement;
        bindElement.hidden = true;

        const template = document.getElementById(this.templateId);
        bindElement.appendChild(template.content.cloneNode(true));

        this.canvas = document.getElementById('ps-canvas');
        // bindElement.appendChild(this.canvas);
        this.canvas.addEventListener('click', event => this.onCanvasClick(event));
        this.canvas.addEventListener('mousedown', event => this.startMove(event));


        this.controls = {
            controls:       document.getElementById('point-selector-controls'),
            zoomIn:         document.getElementById('ps-zoom-in'),
            zoomOut:        document.getElementById('ps-zoom-out'),
            zoom:           document.getElementById('ps-zoom-value'),
            draw:           document.getElementById('ps-draw'),
            move:           document.getElementById('ps-move'),
        };

        this.controls.zoomIn        .addEventListener('click', () => this.updateZoom(2));
        this.controls.zoomOut       .addEventListener('click', () => this.updateZoom(0.5));
        this.controls.draw          .addEventListener('click', () => this.updateMode(true));
        this.controls.move          .addEventListener('click', () => this.updateMode(false));
    }

    updateMode(value) {
        this.drawing = value;

        const newClass = value ? 'drawing' : 'moving';
        const oldClas = !value ? 'drawing' : 'moving';

        this.canvas.classList.add(newClass);
        this.canvas.classList.remove(oldClas);

        if(value) {
            this.controls.draw.classList.add('toggled-button');
            this.controls.move.classList.remove('toggled-button');
        } else {
            this.controls.move.classList.add('toggled-button');
            this.controls.draw.classList.remove('toggled-button');
        }
    }

    loadImage(image) {
        this.bindPoint.hidden = false;
        this.image = image;
        setResolution(this.canvas, this.image.width, this.image.height);

        this.drawImage();
        this.updateZoomValueDisplay();
        this.updateMode(true);
        this.controls.controls.hidden = false;
    }

    updateZoom(factor) {
        this.zoomFactor = Math.max(this.zoomFactor * factor, 1);
        this.redraw();
        this.updateZoomValueDisplay();
    }

    startMove(event) {
        if(!this.drawing && event.button === 0) {
            this.canvas.addEventListener('mousemove', this.moveHandler);
            document.body.addEventListener('mouseup', e => {
                if(e.button === 0) {
                    this.canvas.removeEventListener('mousemove', this.moveHandler);
                }
            });
        }
    }

    ensureBounds() {
        this.imgOffset.x = inRange(this.imgOffset.x, this.image.width - this.getSourceWidth());
        this.imgOffset.y = inRange(this.imgOffset.y, this.image.height - this.getSourceHeight());

    }

    moveSelection(event) {
        this.imgOffset.x -= event.movementX;
        this.imgOffset.y -= event.movementY; 

        this.redraw();
    }

    redraw() {
        this.ensureBounds();
        this.drawImage();
        this.drawAllPoints();
    }

    updateZoomValueDisplay() {
        this.controls.zoom.innerText = `${this.zoomFactor * 100}%`
    }


    getSourceHeight() {
        return Math.trunc(this.image.height / this.zoomFactor);
    }
    getSourceWidth() {
        return Math.trunc(this.image.width / this.zoomFactor);
    }

    drawImage() {
        const sourceWidth = this.getSourceWidth();
        const sourceHeight = this.getSourceHeight();

        const ctx = this.canvas.getContext('2d');
        canvasDisableSmoothing(ctx);
        ctx.drawImage(this.image, this.imgOffset.x, this.imgOffset.y, sourceWidth, sourceHeight, 0, 0, this.canvas.width, this.canvas.height);
    }

    drawAllPoints() {
        this.selectedPoints.forEach(point => this.drawPointSelection(point));
    }

    onCanvasClick(event) {
        if(!this.drawing) {
            return;
        }

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const pixel_x = canvasPos2Pixel(x, rect.width, this.getSourceWidth(), this.imgOffset.x);
        const pixel_y = canvasPos2Pixel(y, rect.height, this.getSourceHeight(), this.imgOffset.y);
        // Si agregas un punto, perdes los redo
        this.redoPoints.length = 0;

        this.addPointSelection({ x: pixel_x, y: pixel_y });
        this.onClickCallback();
    }

    addPointSelection(point) {
        point.prev = this.selectedPoints.length > 0
            ? this.selectedPoints[this.selectedPoints.length - 1]
            : null
            ;
        this.selectedPoints.push(point);

        // this.updateInterface();
        this.drawPointSelection(point);
    }

    drawPointSelection(point) {
        const ctx = this.canvas.getContext("2d");

        const sourceWidth = this.getSourceWidth();
        const sourceHeight = this.getSourceHeight();

        // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
        const x = pixel2CanvasPos(point.x + 0.5, this.canvas.width, sourceWidth, this.imgOffset.x);
        const y = pixel2CanvasPos(point.y + 0.5, this.canvas.height, sourceHeight, this.imgOffset.y);

        // Line
        if (point.prev) {
            const prev = point.prev;
            const prevX = pixel2CanvasPos(prev.x + 0.5, this.canvas.width, sourceWidth, this.imgOffset.x);
            const prevY = pixel2CanvasPos(prev.y + 0.5, this.canvas.height, sourceHeight, this.imgOffset.y);
            drawLine(ctx, prevX, prevY, x, y, POINT_COLOR)
        }

        drawPoint(ctx, x, y, POINT_COLOR, pointSize);
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
        this.onClickCallback()
    }

    redoPoint() {
        if (redoPoints.length > 0) {
            const point = redoPoints.pop();
            addPointSelection(point)
        }
        this.onClickCallback()
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

}
