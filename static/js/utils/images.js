// In case of error returns error message
import {UTIF} from "../libs/UTIF.js";

export async function* imageIterator(images) {
    for(const image of images) {
        switch(image.type) {
            case 'image/tiff': {
                const buffer = await image.arrayBuffer();
                const ifds = UTIF.decode(buffer);
                for(const [i, ifd] of ifds.entries()) {
                    UTIF.decodeImage(buffer, ifd, ifds);

                    const rgbaData = UTIF.toRGBA8(ifd);
                    const imageData = new ImageData(new Uint8ClampedArray(rgbaData), ifd.width, ifd.height);

                    const drawable = document.createElement('canvas');
                    drawable.width = ifd.width;
                    drawable.height = ifd.height;

                    // Rendereamos la imagen en un canvas intermedio para luego poder escalar la imagen
                    const ctx = drawable.getContext('2d');
                    ctx.putImageData(imageData, 0, 0, 0, 0, ifd.width, ifd.height);
                    
                    yield {data: drawable, name: getName(image.name, i, ifds.length)};
                }
            } break;
            case 'image/jpeg':
            case 'image/jpg':
            case 'image/png': {
                yield {data: createImageBitmap(image), name: image.name};
            } break;
            default:
                // Ignoramos tipos que no conocemos
        }
    }
}

function getName(fileName, index, length) {
    if(length > 1) {
        const name = fileName.substring(0, fileName.lastIndexOf('.'));
        const number = `${index}`.padStart(Math.floor(length/10), '0');
        const fType = fileName.substring(fileName.lastIndexOf('.'));
        return name + number + fType;
    }
    return fileName;
}

export function closeImage(frame) {
    if(frame instanceof ImageBitmap) {
        frame.close()
    }
}
