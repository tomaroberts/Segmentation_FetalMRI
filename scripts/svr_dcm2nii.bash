#!/bin/bash

### SVRTK - fetal brain reconstruction
#
# Reconstructs 4D SVR dicom from 2D multi-slice dicom data
#
# Input:
# - multi-slice, multi-stack dicom files
#
# Output:
# - 4D SVR dicom
#
# Requires:
# - sudo apt install dcm2niix pigz
#
# Alena Uus   (alena.uus@kcl.ac.uk)
# Tom Roberts (t.roberts@kcl.ac.uk)
#
###########################################################

PATH="$PATH:/home/MIRTK/build/bin:/home/MIRTK/build/lib/tools"

### Unpack dicoms
svrFolder=/mnt/c/TempInputSeries/
dcmFolder=/mnt/c/TempInputSeries/DICOM/
niiFolder=/mnt/c/TempInputSeries/nii/
mkdir $niiFolder

dcm2niix -z y -o $niiFolder -f %t_%v_%s_%p $svrFolder


# Rename nifti files, move to SVR folder
cd $niiFolder
niiFilenames=(`ls *.nii.gz`)
numNiiFiles=`ls *.nii.gz | wc -l` # nb: assumes series numbers end with 01, i.e.: 601, 701, etc.

# iF=0
# stackFileNumberCtr=1
# while [ $iF -lt $numNiiFiles ] ; do
	
	# # rename stack*.nii.gz
	# mv ${niiFilenames[$iF]} stack$stackFileNumberCtr.nii.gz

	# iF=`expr $iF + 1`
	# stackFileNumberCtr=`expr $stackFileNumberCtr + 1`

# done

# mv stack*.nii.gz $svrFolder
# cd $svrFolder



# # ### Convert dicom to nifti

# # dcmZipFilename=`ls *.zip`
# # unzip -n $dcmZipFilename

# # dcmFoldernames=(`ls -d */`) # assumes no other folders in dir
# # numDcmFolders=`ls -d */ | wc -l`

# # iF=0
# # stackFileNumberCtr=1
# # while [ $iF -lt $numDcmFolders ] ; do
	
	# # # enter dcm folder
	# # cd ${dcmFoldernames[$iF]}
	# # dcmFilename=`ls *.dcm`

	# # # convert dcm2nii
	# # dcm2niix $dcmFilename

	# # # convert .nii to .nii.gz
	# # niiFilename=`ls *.nii`
	# # gzip $niiFilename
	# # niiFilename=`ls *.nii.gz`

	# # # move to original directory / rename / tidy
	# # cp $dcmFilename ..
	# # cp $niiFilename ..
	# # cd ..
	# # mv $dcmFilename stack$stackFileNumberCtr.dcm
	# # mv $niiFilename stack$stackFileNumberCtr.nii.gz

	# # iF=`expr $iF + 1`
	# # stackFileNumberCtr=`expr $stackFileNumberCtr + 1`

# # done

# # rm -r ${dcmFoldernames[@]}



# ### Template selection

# # TODO - Options:
# # - manual - script?
# # - automated - based on slice NCC in all masked stacks (requires CNN-based localisation/segmentation)

# TEMPLATE_FOR_MASKING="stack1.nii.gz"



# ### Create brain mask

# # TODO - Options:
# # - manual segmentation with ITK-Snap - using .dcm or .nii? Just need to ensure mask volume consistent with image volumes
# # - automatic segmentation with neural network


# # Manual segmentation 
# /home/MIRTK/build/bin/mirtk initialise_volume ${TEMPLATE_FOR_MASKING} mask_for_template.nii.gz
# /home/tools/irtk/region mask_for_template.nii.gz mask_for_template.nii.gz -Rt1 0 -Rt2 1
# /home/tools/itksnap/bin/itksnap -g ${TEMPLATE_FOR_MASKING} -s mask_for_template.nii.gz



# ### Perform SVR

# mkdir out-svr-brain
# cd out-svr-brain

# RECON="../SVR-output-brain.nii.gz"
# NUMSTACKS=`ls ../stack*.nii.gz | wc -l`
# STACKS="../stack*.nii.gz"
# TEMPLATE="../stack1.nii.gz"
# ITKSNAP_MASK=../mask_for_template.nii.gz
# THICKNESS=(2.5 2.5 2.5 2.5) # TODO: automate
# ITERATIONS=3
# RESOLUTION=0.85


# echo ".........................................................."
# echo ".........................................................."
# echo "Running SVR reconstruction of fetal brain ..."
# echo


# CMD="/home/MIRTK/build/bin/mirtk reconstruct $RECON $NUMSTACKS $STACKS -template $TEMPLATE -mask $ITKSNAP_MASK -thickness ${THICKNESS[@]} -resolution $RESOLUTION -iterations $ITERATIONS -svr_only -remote "

# echo $CMD > recon.bash
# eval $CMD



# ### Convert SVR nifti to dicom
# echo ".........................................................."
# echo ".........................................................."
# echo "Running SVR nifti to dicom conversion ..."
# echo

# python3.5 /home/scripts/svr_nii_to_dicom.py

# echo ".........................................................."
# echo ".........................................................."



# ### View SVR dicom
# # /home/tools/itksnap/bin/itksnap dcm-svr/IM_0001


