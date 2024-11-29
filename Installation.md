# Installation Instructions for KU Polls

1. Clone the repository
   ```
   git clone https://github.com/pannlnwza/bookstore.git
   ```
2. Change directory into the repo
   ```
   cd bookstore
   ```

3. Activate the virtual environment using one of the following commands, depending on your operating system

    ```shell
    python -m venv env
    ```
    - **Windows**
    
      ```shell
      env\Scripts\activate
      ```
    
    - **macOS/Linux**
    
        ```shell
        source env/bin/activate
        ```

4. Install the required packages using pip
   ```shell
   pip install -r requirements.txt
   ```

5. Run migrations
   ```shell
   python manage.py migrate
   ```
   
6. Load fixture data
   - If you want raw data with no fake user reviews, sales.   
   ```shell
   python manage.py loaddata data/genres.json data/books.json data/stocks.json data/users.json
   ```
   - If you want occupied data.
   ```shell
   python manage.py loaddata data/all_data.json
   
7. Start the Django server
   ```shell
   python manage.py runserver
   ```
