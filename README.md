## CSV to EAD instructions

### Requirements
* Python 2.7+ (has been tested with 2.7 and 3.6.4)

### Use
Download or clone the script.

At the command line:
`python csv_to_ead.py` followed by the filename(s) of the csv files you wish to
convert (multiple filenames can be provided, separated by a space, and processed
 at once)

The script expects a UTF-8 encoded csv file and will validate the headers before
it processes the contents. The only required fields are level_type and level,
which need to be present in either the first or second column (it doesn't matter
which one is in which column, they just both need to be present for the script to
function). The script will validate against the following column headers and map
to the corresponding elements in the EAD:
* level_type (ead:c @level=collection, series, subseries, etc.) _required_
* level (depth of c: 1, 2, 3, etc.) _required_
* unittitle (ead:unittitle, may contain <title render="\*"\> elements)
* date (ead:unitdate)
* date_begin (ead:unitdate @normal before the /)
* date_end (ead:unitdate @normal after the /)
* box (value of ead:container with @type="Box")
* folder (value of ead:container with @type="Folder")
* digital_file (value of ead:container with @type="Digital_file")
* oversize (value of ead:container with @type="Oversize")
* instance_type (ead:container @label value)
* general_note (ead:odd)
* accessrestrict (ead:accessrestrict)
* userestrict _will validate but output has not been implemented yet_
* scopecontent _will validate but output has not been implemented yet_

The script does not construct a fully valid EAD, just the container list (the `<dsc>`
section of the finding aid). 
