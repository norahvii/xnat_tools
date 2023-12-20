#!/bin/bash
#
#================================================================
# set_dca_mrstatus_jsession.sh
#================================================================
#
# Set a single DCA MR Status using a JSESSION token
#
# Usage: ./set_dca_mrstatus.sh <jsession> <session_id> "<mr_status>" "<mr_notes>"
#
# Required inputs:
# <jsession> - A JSESSION token of someone who has access to set statuses
#           (probably Sarah)
# <session_id> - accession number of MR session to set status for
# <mr_status> - MR status to set IN QUOTES
# <mr_notes> - MR notes to set in quotes
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
#startSession() {
#    # Authentication to XNAT and store cookies in cookie jar file
#    local COOKIE_JAR=.cookies-$(date +%Y%M%d%s).txt
#    curl -k -s -b JSESSIONID=${JSESSION_TOKEN} --cookie-jar ${COOKIE_JAR} "${SITE}" > /dev/null
#    echo ${COOKIE_JAR}
#}

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

# Ends the user session.
#endSession() {
#    # Delete the JSESSION token - "log out"
#    curl -i -k --cookie ${COOKIE_JAR} -X DELETE "${SITE}/data/JSESSION"
#    #rm -f ${COOKIE_JAR}
#}

# usage instructions
if [ ${#@} == 0 ]; then
    echo ""
    echo "XNAT set single DCA MR Status - with JSESSION token"
    echo ""
    echo "This script sets the MRStatus and MRNotes custom variable values for a single specified MR session on DCA. Requires a JSESSION token from someone who has permissions to update statuses on DCA"
    echo ""   
    echo "Usage: $0 <jsession_token> <session_id> \"<mr_status>\" \"<mr_notes>\""
    echo "<jsession_token>: A JSESSION token from someone who has permission to update statuses on DCA"   
    echo "<session_id>: The accession number of the MR session e.g. DIANTU_E123456"   
    echo "<mr_status>: The MR status to set MUST BE IN DOUBLE QUOTES"   
    echo "<mr_notes>: The MR notes to set MUST BE IN DOUBLE QUOTES"   
else 

    # Get the input arguments
    JSESSION_TOKEN=$1
    EXPERIMENT_ID=$2
    mrstatus_string=$3
    mrnotes_string=$4
    SITE=https://dca.wustl.edu

    # Read in password
    #read -s -p "Enter your password for accessing data on ${SITE} as ${USERNAME}:" PASSWORD
    echo "JSESSION token is: ${JSESSION_TOKEN}"
    echo ""

    #COOKIE_JAR=$(startSession)

    if [ "${mrstatus_string}" != "null" ] && [ "${mrstatus_string}" != "Usable" ] && [ "${mrstatus_string}" != "1.5T Scanner" ] && [ "${mrstatus_string}" != "FreeSurfer Pipeline Failure" ] && [ "${mrstatus_string}" != "FreeSurfer QC Failure" ] && [ "${mrstatus_string}" != "T1 Scan QC Failure" ] && [ "${mrstatus_string}" != "T1 Unavailable" ] && [ "${mrstatus_string}" != "Waiting for MR Scan QC" ]; then
    	echo "MR Status string must be EXACTLY one of the following:"
    	echo "null (if you want to remove the status)"
        echo "Usable"
    	echo "1.5T Scanner"
    	echo "FreeSurfer Pipeline Failure"
    	echo "FreeSurfer QC Failure"
    	echo "T1 Scan QC Failure"
    	echo "T1 Unavailable"
    	echo "Waiting for MR Scan QC"
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
	echo "Updating MRStatus and MRNotes custom variable for experiment ${EXPERIMENT_LABEL}."
	echo ""
	echo "Setting MRStatus to ${mrstatus_string}"
	echo "Setting MRNotes to ${mrnotes_string}"
	echo ""
	# Examples of what non-url-encoded custom variable pulls from a XNAT URL look like:
	# xnat:subjectData/fields/field[name=Is_ADOPIC_Participant]/field=true
	# xnat:subjectData/fields/field[name=petstatus]/field
	# In the URL we send via CURL we want to encode the equals sign and brackets
	# xsiType (xnat:subjectData below) should be changed based on what level the custom variable is set on
	mrstatus_str_esc=`echo ${mrstatus_string} | sed 's/ /%20/g'`
	mrnotes_str_esc=`echo ${mrnotes_string} | sed 's/ /%20/g'`
	mrnotes_str_esc=`echo ${mrnotes_str_esc} | sed 's/(/%28/g'`
	mrnotes_str_esc=`echo ${mrnotes_str_esc} | sed 's/)/%29/g'`
	mrnotes_str_esc=`echo ${mrnotes_str_esc} | sed 's/=/%3D/g'`
	mrnotes_str_esc=`echo ${mrnotes_str_esc} | sed 's/:/%3A/g'`

	echo ${mrstatus_str_esc}
	echo ${mrnotes_str_esc}

	SET_CUSTOMVAR_URL="${SITE}/data/projects/${PROJECT_ID}/subjects/${SUBJECT_ID}/experiments/${EXPERIMENT_ID}?xnat:mrSessionData/fields/field%5Bname%3Dmrstatus%5D/field=${mrstatus_str_esc}&event_reason=setting%20imaging%20core%20mrstatus"
	echo "Going to set the custom variable with URL: ${SET_CUSTOMVAR_URL}"

	echo "Using curl command:"
	echo "curl -H 'Expect:' -k -b \"JSESSIONID=${JSESSION_TOKEN}\" -X PUT ${SET_CUSTOMVAR_URL}"
	curl -H 'Expect:' -k -b "JSESSIONID=${JSESSION_TOKEN}" -X PUT ${SET_CUSTOMVAR_URL}
	echo ""

	SET_CUSTOMVAR_URL="${SITE}/data/projects/${PROJECT_ID}/subjects/${SUBJECT_ID}/experiments/${EXPERIMENT_ID}?xnat:mrSessionData/fields/field%5Bname%3Dmrnotes%5D/field=${mrnotes_str_esc}&event_reason=setting%20imaging%20core%20mrstatus"
	echo "Going to set the custom variable with URL: ${SET_CUSTOMVAR_URL}"

	echo "Using curl command:"
	echo "curl -H 'Expect:' -k -b \"JSESSIONID=${JSESSION_TOKEN}\" -X PUT ${SET_CUSTOMVAR_URL}"
	curl -H 'Expect:' -k -b "JSESSIONID=${JSESSION_TOKEN}" -X PUT ${SET_CUSTOMVAR_URL}
	echo ""        

	echo "Done with ${EXPERIMENT_LABEL}."
fi

#endSession