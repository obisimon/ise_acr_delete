from __future__ import annotations
import json

from typing import Optional

import base64
import math
import requests
from urllib.parse import urlencode, urljoin

__all__ = ["IseUiApi"]


API_BASE_URL = f"/dna/intent/api//"
AUTH_URL = f"/admin/LoginAction.do"


class IseUiApiException(Exception):
    pass


class IseUiApi(object):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        auth_type: str,
        verify: Optional[bool] = None,
        proxies: Optional[list] = None,

    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.auth_type = auth_type
        self.token = None
        self.session = None
        self._base_url = urljoin("https://", host)
        if verify is not None:
            self.verify = verify
        else:
            self.verify = True
        if proxies:
            self.proxies = proxies


    def _reset_token(self) -> None:
        self.token = None

    def _login(self) -> None:
        if self.session is None or self.token is None:
            self.session = requests.Session()

            self.session.headers.update(
                {
                    "Origin": self._base_url,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Safari/537.36",  # noqa: E501
                }
            )

            if self.proxies:
                self.session.proxies = self.proxies

            response = self.session.post(
                urljoin(self._base_url, AUTH_URL),
                data=urlencode(
                    {
                        "username": self.username,
                        "password": self.password,
                        "authType": self.auth_type,
                        "name": self.username,
                        "rememberme": "on",
                        "locale": "en",
                        "hasSelectedLocale": "false",
                    }
                ),
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",  # noqa: E501
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": urljoin(self._base_url, "/admin/login.jsp"),
                },
                verify=self.verify,
            )

            if response.status_code != 200:
                raise IseUiApiException(f"{response.status_code} {response.text}")

    def _logout(self) -> None:
        self.session.get(
            urljoin(self._base_url, "/admin/logout.jsp"),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",  # noqa: E501
            },
        )

    def _total_endpoints(self, qph: dict[str, str] = None) -> int:
        if qph is None:
            response = self.session.get(
                urljoin(self._base_url, "/admin/rs/uiapi/visibility/fetchMetricData/totalEndpoints"),
                headers={
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
            )
        else:
            qph.update(
                {
                    "startAt": 1,
                    "pageSize": 1,
                }
            )
            qph_header: str = str(
                base64.b64encode(urlencode(qph).encode("utf-8")),
                "utf-8",
            )
            response = self.session.get(
                urljoin(self._base_url, "/admin/rs/uiapi/visibility"),
                headers={
                    "_QPH_": qph_header,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
            )

        if response.status_code != 200:
            raise IseUiApiException(f"{response.status_code} {response.text}")

        if qph is None:
            return int(response.json().get("attrValue", 0))
        else:
            return int(response.headers.get("Content-Range", "/0").split("/")[1])

    def endpoints(
        self,
        columns: Optional[list[str]] = None,
        filters: Optional[dict[str, str]] = None,
        fetch_all: bool = False,
        start: int = 1,
        page_size: int = 500,
    ) -> list[dict[str, str]]:
        self._login()

        if columns is None:
            columns = ["MACAddress","status","NetworkDeviceName","NAS-Port-Id"]

        # status=CONTEXT_EXTACT_MATCH_connected&MACAddress=CA%3A37

        qph = {
            "columns": ",".join(columns),
            "sortBy": columns[0],
        }

        if filters is not None:
            qph.update(filters)

        total: int = page_size
        if fetch_all:
            if filters is None:
                total = self._total_endpoints()
            else:
                total = self._total_endpoints(qph)

            qph.update(
                {
                    "total_entries": total,
                    "paginated": "true",
                }
            )

        rows = []

        for i in range(start - 1, math.ceil(total / page_size)):
            qph.update(
                {
                    "startAt": i + 1,
                    "pageSize": page_size,
                }
            )
            qph_header: str = str(
                base64.b64encode(urlencode(qph).encode("utf-8")),
                "utf-8",
            )
            response = self.session.get(
                urljoin(self._base_url, "/admin/rs/uiapi/visibility"),
                headers={
                    "_QPH_": qph_header,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
            )
            if response.status_code == 200:
                if len(response.json()) > 0:
                    for line in response.json():
                        rows.append(json.loads(line))
            else:
                raise IseUiApiException(f"error on request: {response.text} ({qph})")

        self._logout()

        return rows
