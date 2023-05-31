# A general language-independent text mining method to extract measurement results from echocardiography documents

The Python implementation of the proposed novel language-independent text mining-based information retrieval method is available at this site. The method was developed to extract numerical measurement results from echocardiography documents.  

### Desription of the method:

The method applies generally applicable text cleaning preprocessing activities and does not rely on any information regarding the structure of the documents and the data recording habits. The method automatically identifies the texts fragments of measurement descriptions, and then by matching them to the elements of standardized terminology, are unified. The methodology allows identifying, correcting and unifying the synonyms, acronyms, and typos. Since the methodology used does not contain any language-dependent implementation elements, the proposed method is suitable for processing echocardiographic findings written in any language.
The method was evaluated on a document set containing more than 20,000 echocardiography reports. During the evaluation 12 relevant echocardiography parameters were extracted from the documents. As a result, an average sensitivity of 0.904, an average specificity of 1.0 and an average F1-score of 0.948 were obtained. The case study sufficiently demonstrated the broad applicability of the method also confirmed by the experts.


In case of using these codes or applying the method please cite the following article:

**Szekér S., Fogarassy G., Vathy-Fogarassy Á. A general text mining method to extract echocardiography measurement results from echocardiography documents. _Artificial Intelligence in Medicine_ (2023): In Press, 102584.**

## Structure of the folders

- src
  - common
    - report_loader
      - report_loader.py: Handles report loading from a 7z file
    - report_processor
      - abstract_report_processor.py: AbstractReportProcessor base class
      - advanced_report_processor.py: AdvancedReportProcessor contains the final processor logic
      - null_report_processor.py: NullReportProcessor returns all reports unprocessed
    - echo_miner.py: Handles dictionary loading, report loading and report processing
  - data
    - \_\_init__.py: contains constants and utilities
    - dictionary.json: contains Hungarian terms and their synonyms
