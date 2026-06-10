# Encoding

Encoding is done with imagemagik.

Since it runs in GMT by default in a container it cannot leverage any GPU acceleration and we are comparing fully CPU only encoding.

This can be seen as unfair in cases like AVIF, which are designed for GPU acceleration.

However all other image formats are typically never GPU accelerated and thus this benchmark style was chosen for comparison.

# Decoding

Browsers can decode images with GPU acceleration.

Since no GPU is available to the browser all rendering should be CPU only.


# Results

Ranking from lowest to highest in terms of Power:

- PNG
- webP
- GIF
- JPG
- AVIF


Ranking from lowest to highest in terms of time:

- JPG
- webP
- AVIF
- GIF
- PNG

[Detailed Dashboard View](https://metrics.green-coding.io/compare.html?ids=81a932bc-04da-443b-93cf-d4d8468de247,a57f1820-884a-4c5f-bb18-a2b63690f323,a0976832-3020-4e8d-ab9d-afff114ac269)
