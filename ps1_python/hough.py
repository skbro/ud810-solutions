import numpy as np
import cv2
import os
import math

def hough_lines_acc(BW, rho_res=1, thetas=np.arange(0, 180, 1)):
    """
    % BW: Binary (black and white) image containing edge pixels
    % RhoResolution (optional): Difference between successive rho values, in pixels
    % Theta (optional): Vector of theta values to use, in degrees
    """
    height, width = BW.shape
    rho_max = math.sqrt(height**2 + width**2)
    rho = np.arange(-math.ceil(rho_max)-1, math.ceil(rho_max), rho_res)
    edge_points = np.transpose(np.nonzero(BW))
    H = np.zeros((len(rho), len(thetas)))
    for x, y in edge_points:
        for idx, theta in enumerate(thetas):
            d = x*math.sin(theta*(math.pi/180)) + y*math.cos(theta*(math.pi/180))
            d_val = int(round(d))
            d_idx = np.where(rho==d_val)[0][0]
            H[d_idx,idx]+=1
    
    return (H, thetas, rho)

def hough_peaks(H1, numpeaks=10, threshold=None, nHoodSize=None):
    """
    Find peaks in a Hough accumulator array.
    % Threshold (optional): Threshold at which values of H are considered to be peaks
    % NHoodSize (optional): Size of the suppression neighborhood, [M N]
    """
    H = H1.copy()
    if(nHoodSize == None):
        nHoodSize = np.array(H.shape)//50 + 1 # 2%
    if(threshold == None):
        threshold = 0.5 * np.max(H)
    
    height, width = H.shape
    hoodY, hoodX = nHoodSize
    H_sort = []
    
    for i in range(numpeaks):
        max_val = np.max(H)
        if(max_val<threshold):
            break
        pos = np.unravel_index(H.argmax(), H.shape)
        x = pos[1]
        y = pos[0]
        H_sort.append([x, y])
        stx = max(0,x-hoodX//2)
        endx = min(width, x+hoodX//2)
        sty = max(0,y-hoodY//2)
        endy = min(height, y+hoodY//2)
        
        H[sty:endy, stx:endx] = 0
    
    if(len(H_sort)==0):
        return []
    return np.array(H_sort)

def hough_lines_draw(img, outfile, peaks, rho, theta):
    """
    Draw lines found in an image using Hough transform.
    % img: Image on top of which to draw lines
    % outfile: Output image filename to save plot as
    % peaks: Qx2 matrix containing row, column indices of the Q peaks found in accumulator
    % rho: Vector of rho values, in pixels
    % theta: Vector of theta values, in degrees
    """
    H = cv2.cvtColor(np.float32(img), cv2.COLOR_GRAY2RGB)
    for theta_idx , rho_idx in peaks:
        theta_idx = int(theta_idx)
        rho_idx = int(rho_idx)
        a = np.cos(theta[theta_idx]*math.pi/180)
        b = np.sin(theta[theta_idx]*math.pi/180)
        x0 = a*rho[rho_idx]
        y0 = b*rho[rho_idx]
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv2.line(H, (x1,y1), (x2,y2), (0,255,0), 2)
        
    cv2.imwrite(os.path.join('output', outfile), H)

def hough_lines_draw2(img, outfile, peaks, rho, theta):
    height, width = img.shape
    H = cv2.cvtColor(np.float32(img), cv2.COLOR_GRAY2RGB)
    for theta_idx, rho_idx in peaks:
        theta_idx = int(theta_idx)
        rho_idx = int(rho_idx)
        ctheta = math.cos(theta[theta_idx]*math.pi/180)
        stheta = math.sin(theta[theta_idx]*math.pi/180)
            
        pt1 = (0, 0)
        pt2 = (0, 0)
        
        # x_cos + y_sin=rho
        if(abs(theta[theta_idx])<1):
            pt1 = (math.floor(rho[rho_idx]), 0)
            pt2 = (math.floor(rho[rho_idx]), height)
        elif(abs(theta[theta_idx])==90):
            pt1 = (0, math.floor(rho[rho_idx]))
            pt2 = (width, math.floor(rho[rho_idx]))
        else:
            # y = mx + c
            m = -ctheta/stheta
            c = rho[rho_idx]/stheta
            
            pt1 = (0, math.floor(c))
            pt2 = (math.floor(-c/m), 0)
            pt3 = (math.floor((height - c)/m), height)
            pt4 = (width, math.floor(m*width + c))
            
        cv2.line(H, pt1, pt2, (0, 255, 0), 2)
        
    cv2.imwrite(os.path.join('output', outfile), H)      
    
def hough_circles_acc(BW, radius):
    """
    Compute Hough accumulator array for finding circles.
    
    % BW: Binary (black and white) image containing edge pixels
    % radius: Radius of circles to look for, in pixels
    """
    
    height, width = BW.shape
    thetas = np.arange(0, 180, 1)
    edge_points = np.transpose(np.nonzero(BW))
    H = np.zeros((width, height))
    for y, x in edge_points:
        for theta in thetas:
            a = x + radius*math.cos(theta*math.pi/180)
            b = y + radius*math.sin(theta*math.pi/180)
            a = int(round(a))
            b = int(round(b))
            if(a>=0 and b>=0 and a<width and b<height):
                H[a,b]+=1

    return H
    
def find_circles(BW, radius_range):
    """
    Find circles in given radius range using Hough transform.
    
    % BW: Binary (black and white) image containing edge pixels
    % radius_range: Range of circle radii [min max] to look for, in pixels
    """
    
    centers = []
    radii = []
    
    cnt=0
    for r in radius_range:
        print(cnt)
        H = hough_circles_acc(BW, r)
        center = hough_peaks(H, 10, threshold=0.75*np.amax(H))
        
        for x in center:
            centers.append(x)
            radii.append(r)
        print(cnt)
        cnt+=1
    return (centers, radii)

def filter_lines(peaks, thetaHood=3, rhoHood=50):
    """
    Look for nearby parallel lines in given set of peaks
    % peaks: List of Theta and Rho
    % thetaHood: Theta Range to look for
    % rhoHood: Rho Range to look for
    """
    
    m,n = peaks.shape
    included = np.zeros(m, dtype=bool)
    for i in range(m):
        if(included[i]==True):
            continue
        theta, rho = peaks[i]
        nearbyIndex = np.where(
            (peaks[:,0] >= theta-thetaHood) & 
            (peaks[:,0] <= theta+thetaHood) & 
            (peaks[:,1] >= rho-rhoHood) & 
            (peaks[:,1] <= rho+rhoHood))[0]
        if(len(nearbyIndex) == 1):
            continue
        for ind in nearbyIndex:
            included[ind]=True
    
    return peaks[np.where(included==True)]
    