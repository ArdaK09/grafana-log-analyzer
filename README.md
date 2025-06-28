# Grafana Log Parser API
**Requires**: Docker Engine 20+ and Python 3.9 for development (if running without Docker).


## Configuration and Docker

Docker image contains two containers as can be seen in _docker-compose.yml_. One container contains the Flask app
(the API), the second runs MongoDB. They are connected via the credentials in the _docker-compose.yml_ file.

### Getting Started
1. Place your grafana logs in the path you have specified in the `Datapath` field of 
_config.yml_.
2. Run the program with `docker-compose up --build` in the terminal.
3. Go to `localhost:2000/` if you haven't changed the `host` or `port` fields in _config.yml_ to see if connection
successful. If it is, you'll receive <mark>"Connection Successful"</mark> and a 200 status code.
    - If you have changed them, you probably know where to go.
4. Navigate to `http://localhost:[your port]`
   - If you have not changed the port number, the URI is http://localhost:2000
   
5. Now, you can start by inserting and processing your files using the following functions.


## Supported Functions
- `/insertQueries`, methods = [GET]
  - Inserts the processed logs under `resources/Data` into the database 
    in the following format: <br>
      { <br>
         "query": *"name of the parent HTTP request"*, <br>
         "details": {*select entries from the `attributes` array* }, <br>
         "called_methods": [ <br>
              { 'name': *name of the method*, <br>
                'time (ms)': *duration of the call* <br>
                (if applicable) 'url': *url* <br>
                (if applicable) 'db.statement': *db.statement* <br>
              }, ... <br>
         ] <br>
     }
> Example: "POST /DCE-CommerceBackend/user/inquireProductsByAccountType" can be passed as
>  "inquireproductsbyaccounttype" or "inquireProducts".

- `/SubMethods/<path: Parent HTTP Request>`, methods=[GET]
    - Takes an argument and searches the database documents for a match in the *query* field. 
    - In the case there are multiple matching documents, selects the first one. 
    - Output: Data consisting of all the matching *called methods* fields and *pa
                                        
> The functions after this point produce their output in `/out/` folder.
> Also, their arguments are not case-sensitive, and they support partial matching, i.e.,
> entering a part of the request will also work. <br>rent HTTP request* details.


- `/RepeatingSubMethods/<path: Parent HTTP Request>`, methods=[GET]
  - Works similarly to _SubMethods_ with the first element of the output being comprehensive information
  regarding the parent HTTP call, however **gives more detailed information about the calls** in descending 
  order of total time in ms alongside _total calls_, _average time_, _total time_, _url_ and more.
  - Does not return the result! Only `{"processed": number of documents}`. Results are produced in `out/`.


- `/RepeatingSubMethods`, methods=[GET]
  - Serves the same purpose as the above path except for the need for a search parameter.
  - Analyzes ever file in `resources/Data/` the same way the above function does and produces their results in `out/`
  - Does not return the result! Only `{"processed": number of documents}`.


- `/ParentMethods/<path: method name>`, methods=[GET]
  - Finds all queries (parent HTTP requests) that invoked the specified submethod and 
    provides them in a list.
