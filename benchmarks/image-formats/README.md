# Encoding

Encoding is done with imagemagik.

Since it runs in GMT by default in a container it cannot leverage any GPU acceleration and we are comparing fully CPU only encoding.

This can be seen as unfair in cases like AVIF, which are designed for GPU acceleration.

However all other image formats are typically never GPU accelerated and thus this benchmark style was chosen for comparison.

# Decoding

Browsers can decode images with GPU acceleration.

Since no GPU is available to the browser all rendering should be CPU only.
