# Two-View 3D Reconstruction for Food Volume Estimation

A Python/Jupyter implementation of **two-view 3D reconstruction and food volume estimation**, based on *Two-View 3D Reconstruction for Food Volume Estimation* by Dehais et al. (2017). Starting from two photographs of a meal, the project estimates the relative camera pose, reconstructs a dense 3D point cloud, segments individual food items, and estimates their volumes.

The example scene contains an **apple, a kiwi, a banana, and a pear** on a plate, with a reference card for recovering metric dimensions. The implementation follows the paper's three main stages, **extrinsic calibration, dense reconstruction, and volume estimation**, with the specific algorithms and adaptations described below.

## Project structure

```text
3DReconstruction/
├── code.ipynb           # Complete reconstruction and volume-estimation notebook
├── pose1.png            # First photograph
├── pose2.png            # Second photograph
├── card_template.png    # Reference-card image used for metric scaling
├── checkerboard/        # Checkerboard calibration images (*.png)
└── README.md            # Project documentation
```

The notebook uses these paths relative to its working directory. No separate scripts, configuration files, or precomputed masks are required by the current workflow.

## Requirements

- Python 3.10 or newer (recommended)
- Jupyter Notebook
- NumPy, pandas, OpenCV, Matplotlib, SciPy, scikit-image, and Numba

Install the dependencies with:

```bash
python -m pip install notebook numpy pandas opencv-python matplotlib scipy scikit-image numba
```

## Usage

Open a terminal in the `3DReconstruction` directory and start Jupyter:

```bash
jupyter notebook
```

Open `code.ipynb` and run the cells **in order, from top to bottom**. The notebook uses intermediate results from previous cells throughout the pipeline and displays its diagnostics and final volume table directly in Jupyter.

The checkerboard photographs must be stored as PNG files inside `checkerboard/`. The two views and the card template must match the filenames shown in the folder layout.

## Method

The implementation is organized around the three stages described in the reference paper.

### 1. Extrinsic calibration

**Camera calibration.** Intrinsic parameters and lens distortion are estimated from checkerboard images with OpenCV. The current calibration target has **17 × 10 inner corners** and a **13 mm square size**. The notebook also includes a focal-length approximation from camera specifications, while the checkerboard calibration matrix is selected for reconstruction.

**Feature correspondence and relative pose.** SIFT features are detected and described in both photographs. Descriptor matches are obtained using symmetric nearest-neighbor matching with FLANN. Corresponding points are used to estimate the essential matrix with RANSAC and recover the cameras' relative rotation and translation direction.

**Metric scale.** Because relative translation is initially known only up to scale, features from `card_template.png` are matched to both views. The portrait-oriented card has physical dimensions **53 mm horizontally × 85 mm vertically** in template coordinates. Card correspondences are checked using homographies; pairwise distances between reconstructed card features and their known metric coordinates provide a distribution of scale estimates. The mode of that distribution determines the translation scale in millimeters.

### 2. Dense 3D reconstruction

**Rectification.** The two undistorted images are transformed using **polar rectification**, based on Pollefeys et al. This aligns corresponding epipolar loci into image rows and allows stereo correspondence searches along those rows.

**Stereo matching.** The notebook estimates the disparity search interval from sparse rectified feature matches, using the central 90% of observed disparities with an additional margin. It computes **5 × 5 Census descriptors** and compares them with Hamming distance, aggregated over a **7 × 7 window**.

**Optimization and refinement.** Stereo correspondence is estimated with **hierarchical scanline dynamic programming**, drawing on Van Meerbergen et al. The cost includes matching dissimilarity, occlusion penalties, and regularization across neighboring scanlines. A multiscale search refines disparity estimates from coarse to finer resolutions; matching is performed in both directions to retain consistent correspondences. The final disparity map is filtered before reconstruction.

**Point-cloud generation.** Rectified matches are mapped back into the original ideal image-coordinate systems. Using the calibrated cameras and metrically scaled relative pose, the notebook triangulates dense correspondences and constructs a 3D point cloud and depth map of the dish and food.

### 3. Food volume estimation

**Food segmentation.** The blue plate is separated from the food to obtain a foreground mask. A **marker-controlled watershed** algorithm then combines the reconstructed depth map with HSV color information. Four depth-guided markers initialize the segmentation; depth and color gradients guide the boundaries, followed by morphological cleanup. The result consists of four binary masks, `food_1` through `food_4`, corresponding to the four visible food regions. These numerical labels do not automatically identify their fruit types.

**Dish surface extraction.** Reconstructed points near the detected plate rim are used to estimate its plane with RANSAC. The reference card provides an estimate of the tabletop plane and normal. The notebook models the dish bottom using its assumed elevation above the table, allowing a common reference surface for all food measurements.

**Food surface extraction.** Valid 3D points are selected separately for each segmented food region and sampled on a regular image grid. A **Delaunay triangulation** generates a surface mesh for each region, with boundary and gap filtering to avoid unsupported triangles.

**Volume calculation.** Following Dehais et al., each food volume is approximated by summing the projected area of each surface triangle multiplied by the average height of its vertices above the modeled dish surface:

$$
V = \sum_{t \in T} A_t\,\frac{h_{t,1}+h_{t,2}+h_{t,3}}{3}.
$$

Here, $A_t$ is the triangle area projected onto the dish plane in **mm²**, and $h_{t,i}$ are its vertex heights in **mm**. The computed result in **mm³** is divided by **1,000** to report **mL**.

## Outputs

Running the notebook produces visualizations of the input images, segmented dish, sparse feature correspondences, calibrated/rectified views, disparity and depth maps, dense 3D point cloud, watershed food regions, dish-plane fit, and reconstructed surface meshes.

The final table reports **one estimated volume per segmented food region**, together with the number of mesh vertices and triangles, projected surface area, and 3D sampling coverage. The notebook also displays the combined volume when all four regions are reconstructed.

## Main parameters

| Parameter | Value in the current notebook | Purpose |
| --- | --- | --- |
| `CHECKERBOARD` | `(17, 10)` | Calibration target's inner corners |
| `SQUARE_SIZE` | `13.0` mm | Physical checkerboard square size |
| `CARD_W`, `CARD_H` | `53`, `85` mm | Reference-card dimensions in portrait template coordinates |
| `FIXED_DISH_AREA` | `2 ** 17` pixels | Target area for dense stereo matching |
| `AGG_WINDOW` | `7` | Matching-cost aggregation window |
| `ALPHA`, `BETA` | `0.002`, `0.25` | Stereo regularization and occlusion terms |
| `N_FOODS` | `4` | Number of watershed segments |
| `PLATE_BOTTOM_ABOVE_TABLE_MM` | `3.0` mm | Assumed dish-bottom offset above the table |
| `TARGET_MESH_POINTS` | `2 ** 12` | Approximate number of samples per food surface |

## Scope and limitations

This is a research implementation rather than a calibrated commercial volume-measurement system. Estimation quality depends on camera calibration, reference-card scale, the texture and visibility of the food, matching quality, segmentation, and the modeled dish surface. Reflective or low-texture areas and occluded portions of rounded fruits can affect the reconstructed surfaces and their estimated volumes.

The approach estimates volume from **visible reconstructed surfaces above a modeled dish bottom**, rather than recovering the complete hidden underside of every object. Its output should therefore be interpreted as a geometric estimate.

## References

1. Dehais, J., Anthimopoulos, M., Shevchik, S., and Mougiakakou, S. (2017). *Two-View 3D Reconstruction for Food Volume Estimation*. IEEE Transactions on Multimedia, 19(5), 1090–1099. [DOI: 10.1109/TMM.2016.2642792](https://doi.org/10.1109/TMM.2016.2642792).
2. Van Meerbergen, G., Vergauwen, M., Pollefeys, M., and Van Gool, L. (2002). *A Hierarchical Symmetric Stereo Algorithm Using Dynamic Programming*. International Journal of Computer Vision, 47, 275–285.
3. Pollefeys, M., Koch, R., and Van Gool, L. (1999). *A Simple and Efficient Rectification Method for General Motion*.
4. Zabih, R., and Woodfill, J. (1994). *Non-parametric Local Transforms for Computing Visual Correspondence*. ECCV.
