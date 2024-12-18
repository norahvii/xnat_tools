These tools are for things XNAT doesn't do natively. 

`download_fs.py` downloads FreeSurfers in bulk.  
`pet_helper.py` assists with choosing PET processing parameters.  
`update_sessions.ipynb` assists with updating session statuses in bulk.  

---

The rest of this `README` is meant as an open-source resource to making FreeSurfer life a little easier.

---


1. My day usually starts by going to the DCA, downloading FreeSurfers, and running this script:

```powershell
scp -r .\*.zip viin@mahler:/data/nil-bluearc/benzinger3/norah/downloads
rm *.zip
```
* This script lives inside my downloads folder and is evoked by typing `.\sendanddelete.ps1`
	* This copies however many FreeSurfers I have to my downloads folder.

---

2. Next I verify the .zip files are present and I unzip the files to the desired location:

```bash
# Unzip 2 DCA
function u2d() {
    unzip -q '*.zip' -d /data/nil-bluearc/benzinger3/norah/qc/DCA/
    rm *.zip
}
```

* This function lives inside my `~/.bashrc` file and is evoked by typing `u2d` for "Unzip to DCA"
	* This unzips all .zip files in the current working directory and quietly `-q` moves them to the destination `-d` directory. Then it removes all the .zip files in the current working directory.

---

3. After changing to the place where I'll be working I run this command:

```bash
# Freesurfer Here
function fh() {
    unset FSFAST_HOME
    unset MNI_DIR
    unset FSL_DIR
    export FREESURFER_HOME=""
    export FREESURFER_HOME=/data/nil-bluearc/benzinger3/programs/FreeSurfer-7.1.1
    export SUBJECTS_DIR=`pwd`
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
}
```

* This function lives inside my `~/.bashrc` file and is evoked by typing `fh` for "FreeSurfer Here"
	* This runs all the required export commands to set up FreeSurfer in the current working directory. 

```freesurfer-linux-centos7_x86_64-7.1.1-20200723-8b40551
Setting up environment for FreeSurfer/FS-FAST (and FSL)
FREESURFER_HOME   /data/nil-bluearc/benzinger3/programs/FreeSurfer-7.1.1
FSFAST_HOME       /data/nil-bluearc/benzinger3/programs/FreeSurfer-7.1.1/fsfast
FSF_OUTPUT_FORMAT nii.gz
SUBJECTS_DIR      /data/nil-bluearc/benzinger3/norah/qc/DCA
FSL_DIR           /usr/local/pkg/fsl6.0
```

* It should automatically print out something which looks like this. It means FreeSurfer is ready to launch.

---

4. Now I am ready to launch FreeSurfer using this command:

```bash
alias qc='FreeviewQC'
```

* This alias  lives inside my `~/.bashrc` file and is evoked by typing `qc` which is a short for `FreeviewQC`
	* This also requires you specify the folder name, for example: `qc 141022_CC38973/
`
---

5. Now let's say that I performed edits on 3 volumes and see the following output in my terminal:

```
/data/nil-bluearc/benzinger3/norah/qc/DCA/141022_CC38973/mri/aparc+aseg.mgz saved successfully.
/data/nil-bluearc/benzinger3/norah/qc/DCA/141022_CC38973/mri/wm.mgz saved successfully.
/data/nil-bluearc/benzinger3/norah/qc/DCA/141022_CC38973/mri/brainmask.mgz saved successfully.
```

* This indicates that I have successfully saved my progress on 3 volumes. I do this regularly.

---

6. After making edits to a volume I will run this command:

```bash
# Zip .mgz 
function mgzip() {
    # Check if directory is provided as argument
    if [ -z "$1" ]; then
        echo "Usage: zip_rwx_mgz directory"
        return 1
    fi
    # Remove trailing slash from directory path if present
    dir="${1%/}"
    # Find all .mgz files with permissions -rwxrwxrwx and add them to the zip file
    find "$dir" -type f -name "*.mgz" -perm -777 -exec zip -r "${dir}.zip" {} +
}
```

* This function lives inside my `~/.bashrc` file and is evoked by typing `mgzip` for ".mgz zip"
	* This also requires you specify the folder name, for example: `mgzip 141022_CC38973/`

In my case, because I edited three volumes, my output looks like this:

```
  adding: 141022_CC38973/mri/wm.mgz (deflated 6%)
  adding: 141022_CC38973/mri/brainmask.mgz (deflated 2%)
  adding: 141022_CC38973/mri/aparc+aseg.mgz (deflated 18%)
```

* This this indicates that the function has found all the most recently adjusted files and zipped them as desired.

---


## Freesurfer Hotkeys


<table border="0">
 <tr>
    <td><b style="font-size:20px">Command</b></td>
    <td><b style="font-size:20px">Action</b></td>
 </tr>
 <tr>
    <td>Alt + N</td> 
    <td>Navigate Tool</td> 
 </tr>
 <tr>
    <td>Ctrl + E</td> 
    <td>Recon Edit Tool</td> 
 </tr>
 <tr>
    <td>Alt + E</td> 
    <td>Voxel Edit Tool</td>
 </tr>
 <tr>
    <td>Ctrl + F</td> 
    <td>Toggle all surfaces</td>
 </tr>
 <tr>
    <td>Alt + C</td> 
    <td>Alternate between volumes/surfaces</td> 
 </tr>
 <tr>
    <td>Ctrl + P</td> 
    <td>Toggle left side menu</td> 
 </tr>
 <tr>
    <td>Ctrl + T</td> 
    <td>Point set edit</td> 
 </tr>
 <tr>
    <td>Ctrl + R</td> 
    <td>Reset View</td> 
 </tr>
 <tr>
    <td>Alt + X</td> 
    <td>Show sagital images</td> 
 </tr>
 <tr>
    <td>Alt + Y</td> 
    <td>Show axial images</td> 
 </tr>
 <tr>
    <td>Alt + Z</td> 
    <td>Show coronal images</td> 
 </tr>
 <tr>
    <td>Alt + A/D</td> 
    <td>Decrease/Increase opacity of currently highlighted volume</td> 
 </tr>
 <tr>
    <td>Ctrl + D</td> 
    <td>Hide brainmask</td> 
 </tr>
 <tr>
    <td>Alt + F</td> 
    <td>Toggle currently highlighted surface</td> 
 </tr>
 <tr>
    <td>Alt + U</td> 
    <td>Show cursor</td> 
 </tr>
</table>

You’ll find other shortcuts under [this link](https://surfer.nmr.mgh.harvard.edu/fswiki/FreeviewGuide/FreeviewReference/FreeviewKeyboardShortcuts). I’ll copy the most useful ones here for convenience:


<table border="0">
 <tr>
    <td><b style="font-size:20px">Command</b></td>
    <td><b style="font-size:20px">Action</b></td>
 </tr>
 <tr>
     <td>Ctrl + W</td>
     <td>Hide White Matter</td>
 </tr>
 <tr>
     <td>Ctrl + S</td>
     <td>Save</td>
 </tr>
 <tr>
     <td>Ctrl + Z</td>
     <td>Undo</td>
 </tr>
 <tr>
     <td>Ctrl + Q</td>
     <td>Exit Freeview</td>
 </tr>
 <tr>
     <td>Ctrl + O</td>
     <td>Load Volume</td>
 </tr>
 <tr>
     <td>Up/Down Arrow Keys or PageUp/PageDown</td>
     <td>Change slice</td>
 </tr>
 <tr>
     <td>Scroll or Drag-Right-Click</td>
     <td>Zoom In/Zoom Out</td>
 </tr>
 <tr>
     <td>Ctrl + Up/Down/Left/Right (arrow keys)</td>
     <td>Moving volume (Panning)</td>
 </tr>
 <tr>
     <td>Alt + V</td>
     <td>Toggle currently highlighted volume</td>
 </tr>
 <tr>
     <td>Shift-Drag Left Click</td>
     <td>Adjust Contrast/Brightness</td>
 </tr>
 <tr>
     <td>Zoom in at current location</td>
     <td>Ctrl-Left-Click (or scroll)</td>
 </tr>
 <tr>
     <td>Zoom out at current location</td>
     <td>Ctrl-Right-Click (or scroll)</td>
 </tr>
</table>

When you’re in Voxel/Recon/ROI edit mode:

<table border="0">
 <tr>
    <td><b style="font-size:20px">Command</b></td>
    <td><b style="font-size:20px">Action</b></td>
 </tr>
 <tr>
    <td>Draw / Fill</td>
    <td>Left Click</td>
 </tr>
  <tr>
    <td>Erase / Erase Fill</td>
    <td>Shift+Left Click</td>
 </tr>
</table>

Above are some popular commands and how to perform FreeSurfer edits. 

Happy FreeSurfing!
