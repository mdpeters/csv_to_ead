## Python script to transform container list data to EAD XML

Validates against the following column headers

* level_type (ead:c @level=collection, series, subseries, etc.) _required_
* level (depth of c: 1, 2, 3, etc.) _required_
* unittitle (ead:unittitle, may contain <title> elements)
* date (ead:unitdate)
* date_begin (ead:unitdate @normal before the /)
* date_end (ead:unitdate @normal after the /)
* box (value of ead:container with type=Box)
* folder (value of ead:container with type=Folder)
* digital_file (value of ead:container with type=Digital_file)
* oversize (value of ead:container with type=Oversize)
* instance_type (container @label value)
* general_note (ead:odd)
* accessrestrict (ead:accessrestrict)
* userestrict
* scopecontent
