// Constants
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#00ff00';

class PointsSelector {
    constructor(onClickCallback) {
        this.image = null;
        this.selectedPoints = [];
        this.redoPoints = [];
        this.imgOffset = { x: 0, y: 0 };
        this.zoomFactor = 1;
        this.onClickCallback = onClickCallback

        this.canvas = document.createElement('canvas');    
    }

    bind(bindElement) {
        bindElement.appendChild(this.canvas);
        this.canvas.addEventListener('click', event => this.onCanvasClick(event));

    }

    loadImage(image) {
        this.image = image;
        setResolution(this.canvas, this.image.width, this.image.height);

        this.drawImage();
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

    onCanvasClick(event) {
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

        // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
        const x = pixel2CanvasPos(point.x + 0.5, this.canvas.width, this.image.width, this.imgOffset.x);
        const y = pixel2CanvasPos(point.y + 0.5, this.canvas.height, this.image.height, this.imgOffset.y);

        // Line
        if (point.prev) {
            const prev = point.prev;
            const prevX = pixel2CanvasPos(prev.x + 0.5, this.canvas.width, this.image.width, this.imgOffset.x);
            const prevY = pixel2CanvasPos(prev.y + 0.5, this.canvas.height, this.image.height, this.imgOffset.y);
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
            selectedPoints.forEach(drawPointSelection)
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
        previewSection.hidden = selectedPoints.length < 2 ? true : false
        undo.style.visibility = selectedPoints.length === 0 ? 'hidden' : 'visible';
        redo.style.visibility = redoPoints.length === 0 ? 'hidden' : 'visible';
        clearError();
    }

}
