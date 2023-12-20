#!/bin/bash
#
#================================================================
# set_dca_petstatus_jsession.sh
#================================================================
#
# Set a single DCA PET Status using a JSESSION token
#
# Usage: ./set_dca_petstatus_jsession.sh <jsession_token> <session_id> "<pet_status>" "<pet_notes>"
#
# Required inputs:
# <jsession> - A JSESSION token of someone who has access to set statuses
#           (probably Sarah)
# <session_id> - accession number of PET session to set status for
# <pet_status> - PET status to set IN QUOTES
# <pet_notes> - PET notes to set in quotes
#
#
# Last Updated: 7/18/2022
# Author: Sarah Keefe
#

# Authenticates credentials against XNAT and returns the cookie jar file name. USERNAME and
# PASSWORD must be set before calling this function.
#   USERNAME="foo"
#   PASSWORD="bar"
#   COOKIE_JAR=$(startSession)
# startSession() {
#     # Authentication to XNAT and store cookies in cookie jar file
#     local COOKIE_JAR=.cookies-$(date +%Y%M%d%s).txt
#     curl -k -s -b JSESSIONID=${JSESSION_TOKEN} --cookie-jar ${COOKIE_JAR} "${SITE}/data/JSESSION" > /dev/null
#     echo ${COOKIE_JAR}
# }

# Gets a resource from a URL.
get() {
    local URL=${1}
    curl -H 'Expect:' --keepalive-time 2 -k -b "JSESSIONID=${JSESSION_TOKEN}" ${URL}
}

# Gets a resource from a URL.
put() {
    local URL=${1}
    echo "curl --verbose -H 'Expect:' --keepalive-time 2 -k -b \"JSESSIONID=${JSESSION_TOKEN}\" -X PUT ${URL}"
    curl --verbose -H 'Expect:' --keepalive-time 2 -k -b "JSESSIONID=${JSESSION_TOKEN}" -X PUT ${URL}
}

# # Ends the user session.
# endSession() {
#     # Delete the JSESSION token - "log out"
#     curl -i -k --cookie ${COOKIE_JAR} -X DELETE "${SITE}/data/JSESSION"
#     #rm -f ${COOKIE_JAR}
# }

# usage instructions
if [ ${#@} == 0 ]; then
    echo ""
    echo "XNAT set single DCA PET Status - using JSESSION token"
    echo ""
    echo "This script sets the PETStatus and PETNotes custom variable values for a single specified PET session on DCA. Requires a JSESSION token from someone who has permissions to update statuses on DCA"
    echo ""   
    echo "Usage: $0 <jsession_token> <session_id> \"<pet_status>\" \"<pet_notes>\""
    echo "<jsession_token>: A JSESSION token from someone who has permission to update statuses on DCA"  
    echo "<session_id>: The accession number of the PET session e.g. DIANTU_E123456"   
    echo "<pet_status>: The PET status to set MUST BE IN DOUBLE QUOTES"   
    echo "<pet_notes>: The PET notes to set MUST BE IN DOUBLE QUOTES"   
else 

    # Get the input arguments
    JSESSION_TOKEN=$1
    EXPERIMENT_ID=$2
    petstatus_string=$3
    petnotes_string=$4
    SITE=https://dca.wustl.edu

    # Read in password
    #read -s -p "Enter your password for accessing data on ${SITE} as ${USERNAME}:" PASSWORD
    echo "JSESSION token is: ${JSESSION_TOKEN}"

    echo ""

    #COOKIE_JAR=$(startSession)

    if [ "${petstatus_string}" != "null" ] && [ "${petstatus_string}" != "Usable" ] && [ "${petstatus_string}" != "MRI Unavailable" ] && [ "${petstatus_string}" != "Nonstandard PET Protocol" ] && [ "${petstatus_string}" != "PET Scan QC Failure" ] && [ "${petstatus_string}" != "Reconstruction Failure" ] && [ "${petstatus_string}" != "PUP Pipeline Failure" ] && [ "${petstatus_string}" != "Requires MRI Segmentation" ] && [ "${petstatus_string}" != "Waiting for PET Scan QC" ]; then
    	echo "PET Status string must be EXACTLY one of the following:"
    	echo "Usable"
    	echo "MRI Unavailable"
    	echo "Nonstandard PET Protocol"
    	echo "PET Scan QC Failure"
    	echo "Reconstruction Failure"
    	echo "PUP Pipeline Failure"
    	echo "Requires MRI Segmentation"
        echo "Waiting for PET Scan QC"
        echo "null (if you want to remove the status)"
    	exit
    fi

    echo "Getting session label information for ${EXPERIMENT_ID}."

    EXPERIMENT_INFO_URL="${SITE}/data/archive/experiments?ID=${EXPERIMENT_ID}&columns=label,subject_ID&format=csv"

    EXPERIMENT_INFO_CSV_OUTPUT=$(get ${EXPERIMENT_INFO_URL})

    EXPERIMENT_INFO_NOHEADER=$(echo -e "$EXPERIMENT_INFO_CSV_OUTPUT" | sed -n '2p')

    EXPERIMENT_LABEL=`echo $EXPERIMENT_INFO_NOHEADER | cut -d, -f3` 
    PROJECT_ID=`echo $EXPERIMENT_INFO_NOHEADER | cut -d, -f5` 
    SUBJECT_ID=`echo $EXPERIMENT_INFO_NOHEADER | cut -d, -f2` 
    echo ""
    echo "The experiment label for ${EXPERIMENT_ID} is ${EXPERIMENT_LABEL}."
    echo "${EXPERIMENT_LABEL} is in project ${PROJECT_ID}, subject ${SUBJECT_ID}."
    echo ""
	echo "Updating PETStatus and PETNotes custom variable for experiment ${EXPERIMENT_LABEL}."
	echo ""
	echo "Setting PETStatus to ${petstatus_string}"
	echo "Setting PETNotes to ${petnotes_string}"
	echo ""
	# Examples of what non-url-encoded custom variable pulls from a XNAT URL look like:
	# xnat:subjectData/fields/field[name=Is_ADOPIC_Participant]/field=true
	# xnat:subjectData/fields/field[name=petstatus]/field
	# In the URL we send via CURL we want to encode the equals sign and brackets
	# xsiType (xnat:subjectData below) should be changed based on what level the custom variable is set on
	petstatus_str_esc=`echo ${petstatus_string} | sed 's/ /%20/g'`
	petnotes_str_esc=`echo ${petnotes_string} | sed 's/ /%20/g'`
	petnotes_str_esc=`echo ${petnotes_str_esc} | sed 's/(/%28/g'`
	petnotes_str_esc=`echo ${petnotes_str_esc} | sed 's/)/%29/g'`
	petnotes_str_esc=`echo ${petnotes_str_esc} | sed 's/=/%3D/g'`
	petnotes_str_esc=`echo ${petnotes_str_esc} | sed 's/:/%3A/g'`

	echo ${petstatus_str_esc}
	echo ${petnotes_str_esc}

	SET_CUSTOMVAR_URL="${SITE}/data/projects/${PROJECT_ID}/subjects/${SUBJECT_ID}/experiments/${EXPERIMENT_ID}?xnat:petSessionData/fields/field%5Bname%3Dpetstatus%5D/field=${petstatus_str_esc}&event_reason=setting%20imaging%20core%20petstatus"
	echo "Going to set the custom variable with URL: ${SET_CUSTOMVAR_URL}"

	echo "Using curl command:"
	echo "curl -H 'Expect:' -k -b \"JSESSIONID=${JSESSION_TOKEN}\" -X PUT ${SET_CUSTOMVAR_URL}"
	curl -H 'Expect:' -k -b "JSESSIONID=${JSESSION_TOKEN}" -X PUT ${SET_CUSTOMVAR_URL}
	echo ""

	SET_CUSTOMVAR_URL="${SITE}/data/projects/${PROJECT_ID}/subjects/${SUBJECT_ID}/experiments/${EXPERIMENT_ID}?xnat:petSessionData/fields/field%5Bname%3Dpetnotes%5D/field=${petnotes_str_esc}&event_reason=setting%20imaging%20core%20petstatus"
	echo "Going to set the custom variable with URL: ${SET_CUSTOMVAR_URL}"

	echo "Using curl command:"
	echo "curl -H 'Expect:' -k -b \"JSESSIONID=${JSESSION_TOKEN}\" -X PUT ${SET_CUSTOMVAR_URL}"
	curl -H 'Expect:' -k -b "JSESSIONID=${JSESSION_TOKEN}" -X PUT ${SET_CUSTOMVAR_URL}
	echo ""        

	echo "Done with ${EXPERIMENT_LABEL}."
fi

#endSession