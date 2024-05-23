## Directory Structure

- `database_interact.py`: Contains functions to interact with databases. It can extract data from MySQL and upload/delete data in Firebase. This file is primarily used during the development stage and is not necessary for the smooth running of the application in production.
- `etl_process.py`: Implements core ETL functions. It extracts, transforms, and loads data from databases. This file is fundamental to the functioning of all other parts of the project.
- `parallel_task.py`: Used solely for testing purposes. It is not directly related to the project's primary functionalities.
- `random_stock_select.py`: Implements the random stock selection experiment. This file contains functions to randomly select stocks for experimental purposes.
- `stfile.py`: The main file for generating the Streamlit web application. It provides an interactive web interface for data visualization and analysis.
- `stock_id.csv`: Contains stock IDs and is used for stock selection and other related processes.