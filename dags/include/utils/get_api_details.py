import requests
def get_api_details(url,payload,file_path):
        response = requests.request(
            url=url,
            headers=payload["headers"],
            method="GET",
            stream=True      
        )
        print(f"The url: {url}, headers:{payload["headers"]}")
        if response.status_code != 200:
            raise Exception(
                f"Download failed: {response.status_code} - {response.text[:300]}"
            )

        with file_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:                
                    f.write(chunk)

        print(f"Downloaded to: {file_path}")
        return str(file_path)

