# Wdrive
## Introduction
Wdrive is a Google Drive client written in Python. 

## Dependencies
You need google drive API client module to run the script. 
Run the following command to install the library using pip:
```
pip install --upgrade google-api-python-client
```
Reference: [Google API Python Quick Start](https://developers.google.com/drive/v3/web/quickstart/python#prerequisites)

## Usage
```python quickstart.py -i```

Initialization of Wdrive. 
Note that this operation will download all the files from your Google Drive. 
An opt-out prior to this command is recommended .

```python quickstart.py -out + [name]```
```python quickstart.py -in + [name]```

Opt out and include the file you don't want to sync. The name can be folder name or file name.

```python quickstart.py -pull```
Get latest updatae from Drive.

```python quickstart.py -push```
Push your local changes to the cloud.

## Known Issue
If there is multiple files in your drive that share the same file name, Wdrive cannot handle this case. Please make sure you opt-out the folder containing these files or folders to eliminate abnormalities.

## Author
My name is Wentao Lu and you can contact me at momi2020 at uw.edu. Please let me know if there is any bug in the program or there are some features you'd like to suggest. You can also start a issue in the issue page.

### License
The MIT License (MIT)

Copyright (c) 2016 Wentao Lu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


