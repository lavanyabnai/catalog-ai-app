/**
 * Resize and JPEG-compress an image in the browser using a canvas.
 * Keeps the longest side at maxPx and quality at 0–1.
 * Returns { base64, mediaType } ready to send to the API.
 */
export async function compressImage(
  file: File,
  maxPx = 1200,
  quality = 0.82
): Promise<{ base64: string; mediaType: string }> {
  const bitmap = await createImageBitmap(file);

  const { width, height } = bitmap;
  const scale = Math.min(1, maxPx / Math.max(width, height));
  const w = Math.round(width * scale);
  const h = Math.round(height * scale);

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, w, h);
  bitmap.close();

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) { reject(new Error("Canvas compression failed")); return; }
        const reader = new FileReader();
        reader.onload = () =>
          resolve({
            base64: (reader.result as string).split(",")[1],
            mediaType: "image/jpeg",
          });
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      },
      "image/jpeg",
      quality
    );
  });
}
