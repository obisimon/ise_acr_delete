from urllib.parse import urljoin, parse_qsl
import click
from ise_api.esrapi import IseAPI, IseAPIException
from ise_api.uiapi import IseUiApi, IseUiApiException
import settings
import json
import re
from tabulate import tabulate
import jmespath
from csv import DictWriter


@click.group("")
def cli() -> None:
    """CLI Top level"""


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Choice(["plain", "csv", "json"], case_sensitive=False),
    default="plain",
)
@click.option("--filter", "-f", type=str)
def sponsor_list(output, filter):
    """List all ISE Sponsor Accounts"""
    ersapi = IseAPI(
        settings.ISE_ERS_URL,
        settings.ISE_ERS_USERNAME,
        settings.ISE_ERS_PASSWORD,
        settings.ISE_SSL_VERIFY,
        settings.PROXIES,
    )
    endpoint = "guestuser/"
    if filter:
        endpoint = urljoin(endpoint, f"?filter={filter}")
    ressources = ersapi.getall(endpoint)

    if output == "json":
        print(json.dumps(ressources))
    elif output == "csv":
        writer = DictWriter(
            output,
            fieldnames=jmespath.search("[0]|keys(@)", ressources).pop("link"),
            delimiter=",",
        )
        writer.writeheader()
        writer.writerows(ressources)
        click.echo(output)
    else:
        click.echo(tabulate(ressources))


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Choice(["plain", "csv", "json"], case_sensitive=False),
    default="plain",
)
@click.option("--filter", "-f", type=str)
@click.option("--columns", "-c", type=str)
def ui_list(output, filter, columns):
    """List Elements over UI API"""
    uiapi = IseUiApi(
        settings.ISE_UI_URL,
        settings.ISE_UI_USERNAME,
        settings.ISE_UI_PASSWORD,
        settings.ISE_UI_LOGINTYPE,
        settings.ISE_SSL_VERIFY,
        settings.PROXIES,
    )

    if columns:
        columns = columns.split(",")
    else:
        columns = None

    if filter:
        filters = dict(parse_qsl(filter))
    else:
        filters = None

    ressources = uiapi.endpoints(columns=columns, filters=filters, fetch_all=True)

    if output == "json":
        print(json.dumps(ressources))
    elif output == "csv":
        writer = DictWriter(
            output,
            fieldnames=jmespath.search("[0]|keys(@)", ressources).pop("link"),
            delimiter=",",
        )
        writer.writeheader()
        writer.writerows(ressources)
        click.echo(output)
    else:
        click.echo(tabulate(ressources))


@cli.command()
@click.option(
    "--filter",
    "-f",
    type=str,
    help="ISE Filter options to select which sponsor accounts should be deleted",
    multiple=True,
)
@click.option(
    "--regex-username", type=str, help="Regular expression to match the usernames"
)
@click.option(
    "--regex-email", type=str, help="Regular expression to match the usernames"
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm to really delete the sponsor accounts and endpoints",
)
@click.option(
    "--endpoints",
    is_flag=True,
    help="Include endpoints of the sponsor accounts",
)
@click.option(
    "--limit", type=int, help="limit amount of accounts to be deleted", default=0
)
def delete_sponsor_accounts(filter, regex_username, regex_email, confirm, endpoints, limit):
    """Delete Sponsor Accounts"""
    delete_endpoints = endpoints

    sponsorapi = IseAPI(
        settings.ISE_ERS_URL,
        settings.ISE_SPONSOR_USERNAME,
        settings.ISE_SPONSOR_PASSWORD,
        settings.ISE_SSL_VERIFY,
        settings.PROXIES,
    )

    ersapi = IseAPI(
        settings.ISE_ERS_URL,
        settings.ISE_ERS_USERNAME,
        settings.ISE_ERS_PASSWORD,
        settings.ISE_SSL_VERIFY,
        settings.PROXIES,
    )

    endpoint = "guestuser"

    if filter:
        filter = "&filter=".join(filter)
        endpoint = urljoin(endpoint, f"?filter={filter}&size=100")

    click.echo("load sponsor accounts")
    users = sponsorapi.getall(endpoint)

    if not confirm:
        click.echo("confirm not set, so this is a dry run")

    count = 0
    has_endpoints = False

    for user in users:
        has_endpoints = False
        # click.echo("---------")
        # click.echo(f"process user: {jmespath.search('name', user)}")
        if regex_username and not re.search(
            regex_username, str(jmespath.search("name", user))
        ):
            continue
        if regex_email:
            detail = sponsorapi.get("guestuser/" + jmespath.search("id", user))
            if not re.search(
                regex_email,
                str(jmespath.search("GuestUser.guestInfo.emailAddress", detail)),
            ):
                continue

        click.echo("---------")
        click.echo(f"process user: {jmespath.search('name', user)}")
        
        for endpoint in ersapi.get(
            "endpoint?filter=portalUser.EQ."
            + str(jmespath.search("name", user))
            + "&page=1&size=100"
        ):
            has_endpoints = True
            # click.echo("Endpoint: " + json.dumps(endpoint))
            if confirm and delete_endpoints:
                ersapi._delete("endpoint/" + jmespath.search("id", endpoint))
                click.echo(f"delete related endpoint {jmespath.search('name', endpoint)} {jmespath.search('id', endpoint)}")
            else:
                click.echo(f"would delete related endpoint {jmespath.search('name', endpoint)} {jmespath.search('id', endpoint)}")
        

        if confirm and has_endpoints and delete_endpoints:
            click.echo(
                f"delete guest user {str(jmespath.search('name', user))} (with endpoints)"
            )
            sponsorapi._delete("guestuser/" + jmespath.search("id", user))
        elif has_endpoints:
            click.echo(
                f"would delete guest user {str(jmespath.search('name', user))}, but endpoints found"
            )
        elif confirm:
            click.echo(
                f"delete guest user {str(jmespath.search('name', user))}"
            )
            sponsorapi._delete("guestuser/" + jmespath.search("id", user))
        else:
            click.echo(
                f"would delete guest user {str(jmespath.search('name', user))}"
            )

        count += 1

        if limit and count >= limit:
            break

    click.echo(f"total {count} accounts deleted")


@cli.command()
def get_all_sponsor_endpoints():
    """Test"""
    ersapi = IseAPI(
        settings.ISE_ERS_URL,
        settings.ISE_ERS_USERNAME,
        settings.ISE_ERS_PASSWORD,
        settings.ISE_SSL_VERIFY,
        settings.PROXIES,
    )

    for endpoint in ersapi.get(
        "endpoint?filter=portalUser.CONTAINS.0"
        + "&page=1&size=100"
    ):
        click.echo("Endpoint: " + json.dumps(endpoint))


if __name__ == "__main__":
    cli()
