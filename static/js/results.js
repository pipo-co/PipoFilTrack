"use strict";

class ResultsViewer {
    constructor(templateId) {
        this.templateId = templateId;
        this.canvas     = document.createElement('canvas');
        this.frames     = [];
        this.index      = 0;
        this.inter_id   = null;
        this.fps        = 3;

        this.controls = null;
    }

    bindViewer(bindElement) {
        bindElement.appendChild(this.canvas);

        const template = document.getElementById(this.templateId);
        bindElement.appendChild(template.content.cloneNode(true));

        this.controls = {
            frame:              document.getElementById('rc-frame'),
            play:               document.getElementById('rc-play'),
            stop:               document.getElementById('rc-stop'),
            nextFrame:          document.getElementById('rc-next_frame'),
            prevFrame:          document.getElementById('rc-prev_frame'),
            frameRateUp:        document.getElementById('rc-frame_rate_up'),
            frame_rate_down:    document.getElementById('rc-frame_rate_down'),
            frame_rate:         document.getElementById('rc-frame_rate_value'),
        };

        this.controls.play              .addEventListener('click', () => this.resumeAnimation());
        this.controls.stop              .addEventListener('click', () => this.stopAnimation());
        this.controls.nextFrame         .addEventListener('click', () => this.drawNextFrame());
        this.controls.prevFrame         .addEventListener('click', () => this.drawPrevFrame());
        this.controls.frameRateUp       .addEventListener('click', () => this.updateFrameRate(1));
        this.controls.frame_rate_down   .addEventListener('click', () => this.updateFrameRate(-1));
    }

    loadResults(frames) {
        this.frames = frames
        
        setResolution(this.canvas, frames[0].width, frames[0].height);

        this.drawFrame();
        this.updateFrameRateNumberDisplay();
    }

    resumeAnimation() {
        this.pauseAnimation();
        this.inter_id = setInterval(() => this.drawNextFrame(), 1000 / this.fps);
    }

    pauseAnimation() {
        if(this.inter_id) {
            clearInterval(this.inter_id);
        }
    }

    updateFrameRate(delta) {
        console.log(this.fps, delta, Math.max(this.fps + delta, 1))
        this.fps = Math.max(this.fps + delta, 1);
        this.resumeAnimation();
        this.updateFrameRateNumberDisplay();
    }

    updateFrameNumberDisplay() {
        this.controls['frame'].innerHTML = `${this.index+1}/${this.frames.length}`
    }

    updateFrameRateNumberDisplay() {
        this.controls['frame_rate'].innerHTML = `${this.fps} fps`
    }

    nextFrame() {
        this.index = (this.index + 1) % this.frames.length;
    }

    prevFrame() {
        this.index = this.index === 0 ? this.frames.length - 1 : this.index - 1;
    }

    drawFrame() {
        this.updateFrameNumberDisplay()
        drawIntoCanvas(this.canvas, this.frames[this.index]);
    }

    drawNextFrame() {
        this.nextFrame();
        this.drawFrame();
    }

    drawPrevFrame() {
        this.prevFrame();
        this.drawFrame();
    }
    
    stopAnimation() {
        this.pauseAnimation()
        this.index = 0
        this.drawFrame();
    }
}