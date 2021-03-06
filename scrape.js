config = require('./config.json')

var planningCenterUser=config.planningCenterUser;
var planningCenterPassword=config.planningCenterPassword;

var ccliUser=config.ccliUser;
var ccliPassword=config.ccliPassword;

var planningCenterLoginPage="https://login.planningcenteronline.com/login/new";
var ccliBaseUrl="https://songselect.ccli.com/Songs/";
var ccliLoginPage="https://profile.ccli.com/account/signin";

var arrHeader="Arrangement:";
var cHeader="Copyrights: © ";
var adminHeader="Administrators:";
var newline="<br>";

var express = require('express');
var bodyParser = require('body-parser')
const axios = require('axios');
const cheerio = require('cheerio');
const puppeteer = require('puppeteer');

var app = express();
app.use(express.urlencoded({extended: true})); 
app.use(express.json());   

function getPage(url){
      var result="";
      axios.get(url).then(response=>{
          result=response.data;
      }).catch(error => {
          result="error getting page url:"+page;
          console.log(result);
      })
      return response.data
}

async function loginPC(browserPage,url){
    await browserPage.goto(url);
    await browserPage.type('#email', planningCenterUser);
    await browserPage.type('#password', planningCenterPassword);
    await browserPage.keyboard.press('Enter');
    await browserPage.waitForNavigation();
    console.log('Logged in, new url:', browserPage.url());
}

async function loginCCLI(browserPage,url){
    await browserPage.goto(url);
    await browserPage.type('#EmailAddress', ccliUser);
    await browserPage.type('#Password', ccliPassword);
    await browserPage.keyboard.press('Enter');
    await browserPage.waitForNavigation();
    console.log('Logged in, new url:', browserPage.url());
}

async function parsePage(pageURL){
      let browser = await puppeteer.launch({headless: true});
      let page = await browser.newPage();
      await loginPC(page,planningCenterLoginPage);
      console.log("Loading page: "+pageURL);
      await page.goto(pageURL, {waitUntil: 'load'});
      await page.waitForSelector('table.data_grid');
      
      let urls = await page.$$eval('.control.arrangement.icon.arrangement', links => {
        return links.map(el => el.href);
      });
      console.log("Grabbing song links:");
      console.log(urls);
      
      let ccliNumbers=[];
      for (i=0;i<urls.length;i++){
        await page.goto(urls[i], {waitUntil: 'load'});
        let num = await page.$eval('div.t-2', myDiv => myDiv.innerHTML);
        let parsed=num.split("|")[0].trim().split(" ")[1].replace("#","");
        console.log("Got CCLI number:"+parsed);
        ccliNumbers.push(parsed);
      }
      
      console.log(ccliNumbers);

      await loginCCLI(page,ccliLoginPage);

      var result="";
      for (let number of ccliNumbers){
        let text=await parseEach(page,ccliBaseUrl+number);
        result=result.concat(text);
      }
      console.log(result);
      await browser.close();
      return result;
}

async function parseNewCcli(ccliURL){
  let browser = await puppeteer.launch({
                    headless: true,
                    args: ['--no-sandbox', '--disable-setuid-sandbox']
                });
  let page = await browser.newPage();
  await loginCCLI(page,ccliLoginPage);
  let text=await parseEach(page,ccliURL);
  await browser.close();
  return text;
}

function getFormattedList(copyrights){
    let found=false;
    let myList=[];
    for (i=0;i<copyrights.length;i++){
        each=copyrights[i];
        if(found){
            if(each=="Catalogs"){
                break;
            }
            myList.push(each);
        }
        if (each=="Copyrights"){
            found=true;
        }
    }
    return myList;
}

function isNumeric(value) {
        return /^-?\d+$/.test(value);
}
    
async function parseEach(page,ccliURL){
      await page.goto(ccliURL, {waitUntil: 'load'});
      let title=await page.$eval('.content-title > h1', myDiv => myDiv.innerHTML);
      let authors = await page.$$eval('.content-title > ul > li > a', links => {
        return links.map(el => el.innerHTML);
      });
      let copyrights = await page.$$eval('.song-meta > ul > li', links => {
        return links.map(el => el.innerHTML);
      });
      var cdate="";

      let clist=getFormattedList(copyrights);
      let split=clist[0].split(" ");
      if(clist.length==1 && isNumeric(split[0])){
        cdate=split[0];
        clist=[split.slice(1,split.length).join(" ")];
      }

      let text=title.toUpperCase();
      let indent="&nbsp;&nbsp;&nbsp;";
      text=text.concat(newline);
      text=text.concat(arrHeader +newline);
      for (i=0;i<authors.length;i++){
        text=text.concat(indent+ authors[i] +newline);
      }
      text=text.concat(cHeader+cdate+newline);
      for (i=0;i<clist.length;i++){
        text=text.concat(indent+ clist[i] +newline);
      }
      text=text.concat(newline);
      //console.log(text);
      return text;
}

var begin='<html><meta name="viewport" content="width=device-width,initial-scale=1.0"><body style="font:14pt arial"><h6>';
var end='</h6></body></html>';

app.post('/doScrape', (req,res) => {
    var pageURL=req.body.PC_URL;
    var singleURL=req.body.CCLI_URL;
    let result="";
    if (pageURL!=""){
      result="Got planningcenter page: "+pageURL;
      console.log(result);
      parsePage(pageURL).then( result =>{
        res.send(begin+result+end);
      });
   }else if(singleURL!=""){
      result="got single page:"+singleURL;
      console.log(result);
      parseNewCcli(singleURL).then( result => {
          res.send(begin+result+end);
      });
    }else{
      console.log("Did not receive any input!");
      result="Did not receive any input!";
      res.send(begin+result+end);
    }
});

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

var server = app.listen(process.env.PORT || 8888, function () {
  var host = server.address().address;
  var port = server.address().port;
  console.log("App listening at http://%s:%s", host, port);
})
