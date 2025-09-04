import numpy as np
import scipy
import pandas as pd
import cv2
from matplotlib import pyplot as plt

# Load two poses of an image
img1 = cv2.imread("/content/drive/MyDrive/IACV Project/Codes/Pose1.jpg")
img2 = cv2.imread("/content/drive/MyDrive/IACV Project/Codes/Pose2.jpg")

cv2.imshow("Image 1", img1)
cv2.imshow("Image 2", img2)