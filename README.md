# ofn-python

## How to Use

To use this project, follow these steps:

1. Create your working environment.
    
    ```sh
    $ pipenv --python 3
    ```

2. Clone repository.
    
    ```sh
    $ git clone https://github.com/savka-stepan/ofn-python.git
    ```

3. Install requirements.
    
    ```sh
    $ pipenv install
    ```

4. Create .env file.
    
    ```sh
    $ touch .env
    ```

5. Save several Environment Variables to .env file.
    
    ```sh
    $ export SMTP_SERVER=<XXX>
    $ export SMTP_SERVER_USER=<XXX>
    $ export SMTP_SERVER_PASSWORD=<XXX>
    $ export OPENFOODNETWORK_API_KEY=<XXX>
    $ export EMAIL_OPENTRANSORDERS=<XXX>
    $ export EMAIL_OFN=<XXX>
    $ export FTP_SERVER=<XXX>
    $ export FTP_USERNAME=<XXX>
    $ export FTP_PASSWORD=<XXX>
    $ export PATH_TO_OFN_PYTHON=<XXX>
    ```

6. Restart environment.
    
    ```sh
    $ pipenv exit
    $ pipenv shell
    ```

7. To save new products into google sheet and update on_hand field:
    
    ```sh
    $ python ofn_python/scripts/get_products.py
    ```

8. To generate opentransorder xml files:
    
    ```sh
    $ python ofn_python/scripts/generate_xml.py
    ```