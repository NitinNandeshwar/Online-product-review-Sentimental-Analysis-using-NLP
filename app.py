# doing necessary imports

from flask import Flask, render_template, request,jsonify
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'
# import logger
# import pandas as pd

def get_soup(url):
    r = requests.get(url)
    soup = bs(r.text, 'html.parser')
    return soup

def list_product(box_link,searchString,db1):
    table = db1[searchString]
    product_list = []
    for i in range(len(box_link)):
        # Checking the product is available or not in stock
        if box_link[i].find_all(True, {"class": "_192laR"}):
            availability = "Temporary Available"
        elif box_link[i].find_all(True, {"class": "u05wbu"}):
            availability = "Comming Soon"
        else:
            availability = "Available"

        # Getting EMI value
        if box_link[i].find_all(True, {"class": "_18hQoS"}):
            EMI = "No Cost EMI"
        else:
            EMI = "No EMI"

        # Getting Discount Value
        if box_link[i].find_all(True, {'class': "_3Ay6Sb"}):
            Discount = box_link[i].find_all('div', {'class': "_3Ay6Sb"})[0].text
        else:
            Discount = 0

        # Getting specifications of product
        spec_list = []

        a = box_link[i].find_all('li', {'class': "rgWa7D"})
        for j in range(len(a)):
            spec_list.append(a[j].text)

        print("length of product", len(spec_list))

        # Getting Product Name
        try:
            product_name = box_link[i].find_all('div', {'class': "_4rR01T"})[0].text
        except:
            product_name = "No name"

        # Getting the rating
        try:
            rating = box_link[i].find_all('div', {'class': "_3LWZlK"})[0].text
        except:
            rating = "No rating"

        # Getting the number of reviews value
        try:
            no_reviews = box_link[i].find_all('span', {'class': "_2_R_DZ"})[0].find_all('span')[-1].text.replace('\xa0',
                                                                                                                 '')
        except:
            no_reviews = "No reviews"

        # getting the product price
        try:
            price = box_link[i].find_all('div', {'class': "_30jeq3 _1_WHN1"})[0].text
        except:
            price = "No price"

        # review link
        try:
            review_link = box_link[i]['href']
        except:
            review_link = "No link"

        product_details = {
            "Product_Name": product_name,
            "availability": availability,
            "Rating": rating,
            "No_of_Reviews": no_reviews,
            "Specification": spec_list,
            "Price": price,
            "Dicount": Discount,
            "EMI": EMI,
            "Review_link": review_link
        }

        product_list.append(product_details)

    # Updating the productlist review_page "href" link
    for i in range(len(product_list)):
        productLink = "https://www.flipkart.com" + product_list[i]["Review_link"]

        # prodRes = requests.get(productLink)  # getting the product page from server
        # prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML
        prod_html = get_soup(productLink)

        box1 = prod_html.find('div', {"class": "col JOpGWq"})
        urllist = []
        for a in box1.find_all('a', href=True):
            urllist.append(a['href'])

        review_link = "https://www.flipkart.com" + urllist[-1]

        product_list[i]["Review_link"] = review_link
        x = table.insert_one(product_list[i])

    return product_list

#### scrapping the comments fro productlist
def Reviews_Content(prod_html1,searchString,db):
    table = db[searchString]
    review_list = []
    box1 = prod_html1.find_all('div', {"class": "_1AtVbE col-12-12"})
    del box1[0:4]
    # getting the comments from the link
    for i in range(len(box1) - 1):
        # print(i)
        # Getting rating
        try:
            rating=box1[i].find_all('div', {"class": "_3LWZlK _1BLPMq"})[0].text
        except:
            rating="No rating"

        # getting product name
        try:
            name=box1[i].find_all('p', {"class": "_2sc7ZR _2V5EHH"})[0].text
        except:
            name="No name"

        # getting buyer
        try:
            buyer= box1[i].find_all('p', {"class": "_2mcZGG"})[0].find_all('span')[0].text
        except:
            buyer="No buyer"

        # getting location details
        try:
            location= box1[i].find_all('p', {"class": "_2mcZGG"})[0].find_all('span')[1].text
        except:
            location="No location"

        # Getting the review heading
        try:
            review_heading= box1[i].find_all('p', {"class": "_2-N8zT"})[0].text
        except:
            review_heading="No heading"

        # getting the likes details
        try:
            likes=box1[i].find_all('span', {"class": "_3c3Px5"})[0].text
        except:
            likes="No likes"

         # getting the dislikes details
        try:
            dislikes=box1[i].find_all('span', {"class": "_3c3Px5"})[1].text
        except:
            dislikes="No dislikes"

        # getting the comments
        try:
            comment= box1[i].find_all('div', {"class": "t-ZTKy"})[0].text.replace("READ MORE", '')
        except:
            comment="No comment"

        review_dict = {
            "Product": searchString,
            "Rating": rating,
            "Name": name,
            "Buyer": buyer,
            "Location": location,
            "Review_heading": review_heading,
            "Likes": likes,
            "Dislikes": dislikes,
            "Comment": comment
        }
        x = table.insert_one(review_dict)
        review_list.append(review_dict)

    return review_list




#searchString = "samsung"



@app.route('/',methods=['POST','GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ","") # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db1= dbConn['product_list']
            db = dbConn['crawlerDB'] # connecting to the database called crawlerDB
            reviews = db[searchString].find({}) # searching the collection with the name same as the keyword
            if reviews.count() > 0: # if there is a collection with searched keyword and it has records in it
                return render_template('results.html',reviews=reviews) # show the results to user
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString # preparing the URL to search the product on flipkart
                uClient = uReq(flipkart_url) # requesting the webpage from the internet
                flipkartPage = uClient.read() # reading the webpage
                uClient.close() # closing the connection to the web server
                flipkart_html = bs(flipkartPage, "html.parser") # parsing the webpage as HTML

                box_link = flipkart_html.findAll('a', {"class": "_1fQZEK"})

                lop=list_product(box_link,searchString,db1)

                # Only Top Product from productlist review
                Top_product = 0
                reviews_comment = []
                for x in range(1, 50):
                    review_link = lop[Top_product]["Review_link"] + (f"&page={x}")
                    html1 = get_soup(review_link)
                    comments = Reviews_Content(html1,searchString,db)  # calling the getting comment function
                    # print("comments:",comments)
                    reviews_comment.append(comments)
                    #   reviews_comment=reviews_comment[0]
                    #print("Length of Comment:", len(reviews_comment))
                    count = len(html1.find_all('a', {"class": "_1LKTO3"}))
                    #print("count:", count)
                    if (count == 2 or x == 1):
                        pass
                    else:
                        break

                flat_list = [item for sublist in reviews_comment for item in sublist]

            return render_template('results.html', reviews=flat_list)  # showing the review to the user
        except:
            return 'something is wrong'
            # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000,debug=True) # running the app on the local machine on port 8000


