from http.client import responses
from typing import Any, Optional
import requests
import json
import jmespath
from urllib.parse import urlencode, urlparse, parse_qsl, urljoin
from requests.models import HTTPBasicAuth
from urllib3 import disable_warnings

disable_warnings()

DEFAULT_PAGE_SIZE = 100


class IseAPIException(Exception):
    pass


class IseAPI:
    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        verify: bool = True,
        proxies: Optional[list] = None,
    ) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
            "Content-Type": "application/json",
            "Accept": "application/json",
            }
        )
        self.session.auth = HTTPBasicAuth(user, password)
        if proxies:
            self.session.proxies = proxies
        if not verify:
            self.session.verify = verify

    def _get(self, url: str) -> dict[str, Any]:
        url = urljoin(self.base_url, url)

        print(f"get: {url}")

        response = self.session.request(
            "GET",
            url,
        )

        if not response.ok:
            raise IseAPIException(f"Accreditation API GET error {response.text}")

        return response.json()

    def get(self, url: str) -> list[dict[str, Any]]:
        url = urlparse(url)
        response = self._get(url.geturl())
        if response.get("SearchResult", {}).get("resources") is not None:
            return response.get("SearchResult", {}).get("resources", [])            
        return response

    def getall(self, url: str) -> list[dict[str, Any]]:
        resources = []
        url = urlparse(url)
        query = dict(parse_qsl(url.query))
        query.update(
            {
                "size": query.get("size", str(DEFAULT_PAGE_SIZE)),
                "page": query.get("page", "1"),
            }
        )
        url = url._replace(query=urlencode(query))
        response = self._get(url.geturl())
        while response.get("SearchResult"):
            resources += response["SearchResult"].get("resources", [])
            if response["SearchResult"].get("nextPage", {}).get("href"):
                response = self._get(response["SearchResult"]["nextPage"]["href"])
            else:
                response = {}

        return resources

    def _delete(self, url: str) -> None:
        url = urljoin(self.base_url, url)
        response = self.session.request(
            "DELETE",
            url,
        )

        if not response.ok:
            raise IseAPIException(f"Accreditation API DELETE error {response.text}")

    def _post(self, url: str, payload: dict[str, Any]) -> None:
        url = urljoin(self.base_url, url)

        response = self.session.request(
            "POST",
            url,
            data=json.dumps(payload),
        )
        if not response.ok:
            raise IseAPIException(
                f"Accreditation API POST error {response.text} {payload}"
            )

    def _put(self, url: str, payload: dict[str, Any]) -> None:
        url = urljoin(self.base_url, url)

        response = self.session.request(
            "PUT",
            url,
            data=json.dumps(payload),
        )
        if not response.ok:
            raise IseAPIException(
                f"Accreditation API PUT error {response.text} {payload}"
            )

    def get_guestuser(self, username: str) -> dict[str, Any]:
        response = self._get(f"guestuser/name/{username}")
        return response

    def upsert_guestuser(
        self,
        username: str,
        password: str,
        fistname: str,
        lastname: str,
        email: str,
        portal_id: str,
        guest_type: str,
        valid_days: int,
        location: str,
        group_tag: str,
        only_add: bool = False,
    ) -> None:
        payload: dict[str, Any] = {
            "GuestUser": {
                "portalId": portal_id,
                "guestType": guest_type,
                "guestInfo": {
                    "enabled": "true",
                    "userName": username,
                    "password": password,
                    "firstName": fistname,
                    "lastName": lastname,
                    "emailAddress": email,
                },
                "guestAccessInfo": {
                    "validDays": valid_days,
                    "location": location,
                    "groupTag": group_tag,
                },
            }
        }
        user: Optional[dict[str, Any]] = None
        try:
            user = self.get_guestuser(username)
        except Exception:
            pass

        if user and not only_add:
            payload["GuestUser"].update({"id": jmespath.search("GuestUser.id", user)})
            self._put(f"guestuser/{jmespath.search('GuestUser.id', user)}", payload)
        elif not user:
            self._post("guestuser/", payload)

    def delete_guestuser(
        self,
        username: str,
    ) -> None:

        user: Optional[dict[str, Any]] = None
        try:
            user = self.get_guestuser(username)
        except Exception:
            pass

        if user:
            self._delete(f"guestuser/{jmespath.search('GuestUser.id', user)}")
