import fs from 'fs';
// @ts-ignore
import dotenv from 'dotenv'; 
dotenv.config(); 

let filter_body = fs.readFileSync('filter_body.json', 'utf8');

type InitJobResponse = {
  job: {
    data: any
    id: string
    status: string
  }
}

async function initJob(): Promise<string> {
  // @ts-ignore
  const res = await fetch("https://manage.wix.com/export-service/v1/export-async-job", {
    // @ts-ignore
    "headers": {
      "accept": "application/json, text/plain, */*",
      "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
      "authorization": process.env.AUTHORIZATION,
      "cache-control": "no-cache",
      "commonconfig": "%7B%22brand%22%3A%22wix%22%7D",
      "consent-policy": "%7B%22func%22%3A1%2C%22anl%22%3A1%2C%22adv%22%3A0%2C%22dt3%22%3A0%2C%22ess%22%3A1%7D",
      "content-type": "application/json",
      "pragma": "no-cache",
      "priority": "u=1, i",
      "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-origin",
      "x-wix-brand": "wix",
      "x-wix-client-artifact-id": "com.wixpress.wixstores-dashboard-product-list",
      "x-xsrf-token": "1723889387|-bloQfT7iv74",
      "cookie": process.env.COOKIE,
      "Referer": "https://manage.wix.com/dashboard/f2c5ef0e-f559-4e93-b364-f3a9a65accbb/wix-stores/products?referralInfo=sidebar&selectedColumns=0%2CName%2CProductType%2CProductSku%2CComparePrice%2CProductInventoryStatus%2CProductRibbon+false%2CProductBrand+false&viewId=all-items-view",
      "Referrer-Policy": "strict-origin-when-cross-origin"
    },
    "body": filter_body,
    "method": "POST"
  });

  let data: InitJobResponse = await res.json() as InitJobResponse
  fs.writeFileSync('newjob.json', JSON.stringify(data))
  return data.job.id
}

async function getStatus(jobId: string): Promise<string> {
  const api = () => fetch(`https://manage.wix.com/export-service/v1/export-async-job/${jobId}?jobId=${jobId}`, {
    // @ts-ignore
    "headers": {
      "accept": "application/json, text/plain, */*",
      "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
      "authorization": process.env.AUTHORIZATION,
      "cache-control": "no-cache",
      "commonconfig": "%7B%22brand%22%3A%22wix%22%7D",
      "consent-policy": "%7B%22func%22%3A1%2C%22anl%22%3A1%2C%22adv%22%3A0%2C%22dt3%22%3A0%2C%22ess%22%3A1%7D",
      "pragma": "no-cache",
      "priority": "u=1, i",
      "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-origin",
      "x-wix-brand": "wix",
      "x-wix-client-artifact-id": "com.wixpress.wixstores-dashboard-product-list",
      "x-xsrf-token": "1723889387|-bloQfT7iv74",
      "cookie": process.env.COOKIE,
      "Referer": "https://manage.wix.com/dashboard/f2c5ef0e-f559-4e93-b364-f3a9a65accbb/wix-stores/products?referralInfo=sidebar&selectedColumns=0%2CName%2CProductType%2CProductSku%2CComparePrice%2CProductInventoryStatus%2CProductRibbon+false%2CProductBrand+false&viewId=all-items-view",
      "Referrer-Policy": "strict-origin-when-cross-origin"
    },
    "body": null,
    "method": "GET"
  });

  while (true) {
    let res = await api()
    let data = await res.json() as InitJobResponse
    if (data.job.status === 'FINISHED') {
      return data.job.status
    }
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

async function getExportInFile(jobId : string): Promise<Boolean> {
  const api = () => fetch(`https://wixmp-32e6f6da09c36ec8bb116976.wixmp.com/QueryProductsOrVariants/msid/f2c5ef0e-f559-4e93-b364-f3a9a65accbb/job_id/${jobId}/catalog_products.csv?token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjgzYThjODBkNTJjYzQ1MGViOWQ5ZWEwZjFhZTc3YWNiIiwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXSwib2JqIjpbW3sicGF0aCI6Ii9RdWVyeVByb2R1Y3RzT3JWYXJpYW50cy9tc2lkL2YyYzVlZjBlLWY1NTktNGU5My1iMzY0LWYzYTlhNjVhY2NiYi9qb2JfaWQvMjZiNTAwYjctN2JiMy00MzYwLTk3NGUtYjNhODQ5YWRjZTNmL2NhdGFsb2dfcHJvZHVjdHMuY3N2In1dXSwiaXNzIjoidXJuOmFwcDo4M2E4YzgwZDUyY2M0NTBlYjlkOWVhMGYxYWU3N2FjYiIsImV4cCI6MTcyMzkwNzc5NywiaWF0IjoxNzIzOTA3MTg3LCJqdGkiOiIyOTdkMWM1My03M2U1LTRjYWEtOTljMi1iZWU2ODJjY2I4NGQiLCJkaXMiOnsiZmlsZW5hbWUiOiJjYXRhbG9nX3Byb2R1Y3RzLmNzdiIsInR5cGUiOiJhdHRhY2htZW50In19.VlbwCX1zBnRnxxxap3YJHRMGsL-Q9rIoQe8V6ZXEDVY&filename=catalog_products.csv`, {
    "headers": {
      "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
      "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
      "cache-control": "no-cache",
      "pragma": "no-cache",
      "priority": "u=0, i",
      "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "document",
      "sec-fetch-mode": "navigate",
      "sec-fetch-site": "cross-site",
      "upgrade-insecure-requests": "1",
      "Referer": "https://manage.wix.com/",
      "Referrer-Policy": "strict-origin-when-cross-origin"
    },
    "body": null,
    "method": "GET"
  });

  let res = await api()
  let data = await res.text()
  fs.writeFileSync('catalog_products.csv', data)
  return true
}

async function main() : Promise<void> {
  let jobId = await initJob()
  console.log(`Job id: ${jobId}`)
  let status = await getStatus(jobId)
  console.log(`Status: ${status}`)
  let success = await getExportInFile(jobId)
  console.log(`Exported: ${success}`)

  return
}

main()