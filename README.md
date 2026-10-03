# Pakistan car number plate dataset

An object-detection dataset exported from Roboflow in YOLO format: 12,322 images at 640x640 with boxes for
37 classes (digits 0-9, letters A-Z and `LicensePlate`), split into train 11,172 / valid 664 / test 486.

Kaggle sources (two listings by the same author, identical contents):

- https://www.kaggle.com/datasets/musakhanalabazy/pakistan-car-number-plate
- https://www.kaggle.com/datasets/musakhanalabazy/pakistan-car-number-plate-data-set

The images (about 630 MB) are not stored in this folder. `prepare_annotations.py` reads the label files from the
extracted download and writes `number_plates_annotations.csv`, one row per annotation. The notebook and report
work from that table.

## Headline numbers

- 12,322 image files, but only 1,748 distinct source images (about 7 files per source on average, median 2, max 54)
- 23,311 annotations: 11,517 plate annotations and 11,794 character boxes
- 4,297 plate annotations (37.3%) are stored as polygons, the rest as boxes; polygons were converted to boxes
- 1,223 images have an empty label file
- After cleaning: 12,273 images, 11,465 plate boxes, 11,793 character boxes

## Other findings

- 249 source images (14.2%) have copies in more than one split; 32 are in all three splits.
- 72.4% of test images (352 of 486) and 42.8% of validation images (284 of 664) come from a source photo that is
  also in the training set.
- The Roboflow readme says no augmentation was applied, but the repeated files are different crops of the same
  photo with noise added, so augmentation happened before the export.
- 63.2% of images have only a plate box, 26.4% have a plate plus characters, 10.0% have no labels and 54 images
  have characters without a plate box.
- Images with character boxes: 24.1% of train, 87.3% of valid, 7.0% of test. The test split has only 101
  character boxes in total (train 9,681, valid 2,011).
- Most common character: A (624 boxes). Rarest: X (152). Most common digit: 7 (393). Rarest digit: 1 (266).
- Z appears in only 60 distinct source images, X in 75.
- 378 images have more than one plate box; the most in one image is 9. The busiest image has 17 boxes.
- The median plate box is 338 x 218 px (16.3% of the image); 35.9% of plate boxes cover more than half the frame
  and 91.8% touch an image edge.
- 49 files are byte-identical copies of another file; 12 of those pairs sit in two different splits and 4 pairs
  carry different labels.
- Reading characters left to right inside the plate box gives 2,875 approximate strings with a median length of 3;
  only 6.5% have the letters-then-digits shape of a standard Pakistani plate.

## Caveats

- Despite the title this is a mixed collection. Some source names look like Pakistani car listings (284 sources),
  others point to other countries, 94 are named `syn_*` and 5 are named after an image generator. The Pakistani
  share could not be measured.
- "Source image" is taken from the file name (the part before `.rf.`). It has not been confirmed on the pixels.
- Only a handful of images were looked at. Label correctness was not checked, and brightness or blur was not measured.
- The plate text reconstruction is approximate (single-line plates with exactly one plate box only). Plate numbers
  identify real vehicles, so no plate strings are printed or saved anywhere, only aggregate counts.
- The shipped split leaks. For any evaluation, regroup images by `source_id` (the cleaned CSV has the columns for it).

## What cleaning changed

Raw table 24,534 rows x 19 columns, cleaned table 24,482 rows x 19 columns.

- polygon rows replaced by their enclosing box (done in `prepare_annotations.py`, flagged in `label_format`)
- 49 byte-identical duplicate images removed, keeping the copy with the fuller annotation
- 13 plate boxes under 2 px wide or tall removed
- unlabelled images kept as one row each with `is_background = True`
- added `name_pattern`, `source_copies`, `source_in_multiple_splits`, `n_boxes`, `n_plates`, `n_chars`

## Folder layout

```
data.yaml, README.dataset.txt, README.roboflow.txt   files shipped with the download
prepare_annotations.py           builds the annotation CSV and the sample sheet from the raw download
number_plates_annotations.csv    one row per annotation, as parsed
number_plates_cleaned.csv        the same after cleaning
number_plates_analysis.ipynb     the analysis, saved with outputs
number_plates_report.pdf         written report
charts/                          PNG charts used in the notebook and report
```

## How to run

The notebook only needs the CSV:

```
cd pakistan_number_plates
../.venv/bin/python -c "import nbformat; from nbclient import NotebookClient; nb = nbformat.read('number_plates_analysis.ipynb', 4); NotebookClient(nb, kernel_name='python3').execute(); nbformat.write(nb, 'number_plates_analysis.ipynb')"
```

or open it in Jupyter and run all cells (working directory = this folder). To rebuild the CSV from the raw download (a folder containing
`train/`, `valid/` and `test/`, each with `images/` and `labels/`):

```
../.venv/bin/python prepare_annotations.py /path/to/extracted/dataset
```
