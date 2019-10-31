[![GitHub (pre-)release](https://img.shields.io/badge/Release-v0.3.4-red.svg)](https://github.com/ktmeaton/NCBImeta/releases/tag/v0.3.1)
[![GitHub license](https://img.shields.io/dub/l/vibe-d.svg?style=flat)](https://github.com/ktmeaton/NCBImeta/blob/master/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/ktmeaton/NCBImeta.svg)](https://github.com/ktmeaton/NCBImeta/issues)


# NCBImeta
Query and create a database of NCBI metadata (includes SRA). 
 
 
## Python Requirements
Python3.4+  
BioPython (1.70)    
PyYAML (5.1.2)

```
pip install --user -r requirements.txt 
```

## Version

Release - Version v0.3.4 (master)  
Development - Version 0.4.0 (dev)  

## Installation

Release:  
```
git clone https://github.com/ktmeaton/NCBImeta.git   
cd NCBImeta  
```   
Development:  
```
git clone -b dev https://github.com/ktmeaton/NCBImeta.git   
cd NCBImeta  
```
## Quick Start Example

### Run the program
```
src/NCBImeta.py --flat --config example/config.yaml
```

### Annotate the database with curated tab-separated text files of metadata
```
src/NCBImeta_AnnotateReplace.py --database example/yersinia_pestis_db.sqlite --annotfile example/annot_1.txt --table BioSample
src/NCBImeta_AnnotateReplace.py --database example/yersinia_pestis_db.sqlite --annotfile example/annot_2.txt --table BioSample
```

Note that the first column of your annotation file MUST be a column that is unique to each record. An Accession number or ID is highly recommended. The column headers in your annotation file must also exactly match the names of your columns in the database.  

NCBImeta_AnnotateReplace.py, as the name implies, replaces the existing annotation with the data in your custom metadata file. If you would like to retain the original metadata from NCBI, and simply concatenate (append) your custom metadata, instead use the NCBImeta_AnnotateConcatenate.py script.  

### Join NCBI tables into a unified master table  
```
src/NCBImeta_Join.py --database example/yersinia_pestis_db.sqlite --anchor BioSample --accessory "BioProject Assembly SRA Nucleotide Pubmed" --final Master --unique "BioSampleAccession BioSampleAccessionSecondary BioSampleBioProjectAccession"
```  

### Export the database to tab-separated text files by table.
```
src/NCBImeta_Export.py --database example/yersinia_pestis_db.sqlite --outputdir example/
```

### Explore!
Explore your database text files using a spreadsheet viewer (Microsoft Excel, Google Sheets, etc.)  
Browse your SQLite database using DB Browser for SQLite (see below for program links)   


## Example output of the command-line interface:  
<img src="https://github.com/ktmeaton/NCBImeta/blob/master/images/NCBImeta_CLI.gif" alt="NCBImeta_CLI" width="700px"/> 


## Currently Supported NCBI Tables  
Assembly  
BioProject  
BioSample  
Nucleotide  
SRA  
Pubmed

## Example database output (a subset of the Assembly table)      
<img src="https://github.com/ktmeaton/NCBImeta/blob/master/images/NCBImeta_DB_small.gif" alt="NCBImeta_DB" width="700px"/> 

## Usage
To customize the search terms and database to your needs, please read through config/README_config.md and schema/README_schema.md.
These two files provide instructions on writing configuration files and customizing metadata.


## Up-Coming Features
- Implement config file as yaml!
- Release packaging with conda.    
- Consider switching from minidom to lxml for XPath and XLST functionality.  
- Database join with EnteroBase metadata?  
- Any requested tables or metadata :)  

## Suggested Accessory Programs
### Database Browser
DB Browser for SQLite: https://sqlitebrowser.org/  

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

See CHANGELOG.md.

## License

This project is licensed under the MIT License - see the LICENSE file for details.    

## Credits

author: Katherine Eaton (ktmeaton@gmail.com)

## Helpful Development Commands  
Merging a development branch into master:  
        (on branch development) `git merge origin/master`
        (resolve any merge conflicts if there are any)  
        `git checkout master`  
        `git merge --no-ff development` (there won't be any conflicts now)  

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
