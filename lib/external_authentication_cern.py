# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""External user authentication for CERN NICE/CRA Invenio."""

__revision__ = \
    "$Id$"

import httplib
import socket

from invenio.external_authentication import ExternalAuth, \
        WebAccessExternalAuthError
from invenio.external_authentication_cern_wrapper import AuthCernWrapper

_managed_exceptions = (httplib.CannotSendRequest,
                        socket.error)

class ExternalAuthCern(ExternalAuth):
    """
    External authentication example for a custom HTTPS-based
    authentication service (called "CERN NICE").
    """


    def __init__(self):
        """Initialize stuff here"""
        ExternalAuth.__init__(self)
        try:
            self.connection = AuthCernWrapper()
        except: # Let the user note that no connection is available
            self.connection = None


    def _try_twice(self, funct, *params):
        try:

            ret = eval("self.connection." + funct+str(params))
        except Exception, e:
            if isinstance(e, _managed_exceptions):
                self.connection = AuthCernWrapper()
                try:
                    ret = eval("self.connection." + funct+str(params))
                except Exception, e:
                    if isinstance(e, _managed_exceptions):
                        raise WebAccessExternalAuthError
                    else:
                        raise e
            else:
                raise e
        return ret


    def auth_user(self, username, password):
        """
        Check USERNAME and PASSWORD against CERN NICE/CRA database.
        Return None if authentication failed, email address of the
        person if authentication succeeded.
        """

        infos = self._try_twice('get_user_info', username, password)
        if "email" in infos:
            self.last_username = username
            self.last_password = password
            self.last_prefs = infos
            return infos["email"]
        else:
            return None

    def user_exists(self, email):
        """Checks against CERN NICE/CRA for existance of email.
        @return True if the user exists, False otherwise
        """
        users = self._try_twice('list_users', email)
        return email.upper() in [user['email'].upper() for user in users]


    def fetch_user_groups_membership(self, email, password=None):
        """Fetch user groups membership from the CERN NICE/CRA account.
        @return a dictionary of groupname, group description
        """
        groups = self._try_twice('get_groups_for_user', email)
        return dict(map(lambda x: (x, '@' in x and x + ' (Mailing list)' \
                        or x + ' (Group)'), groups))


    def fetch_user_preferences(self, username, password=None):
        """Fetch user preferences/settings from the CERN Nice account.
        the external key will be '1' if the account is external to NICE/CRA,
        otherwise 0
        @return a dictionary. Note: auth and respccid are hidden
        """
        prefs = self._try_twice('get_user_info', username, password)
        ret = {}
        for key, value in prefs.items():
            if key in ['auth', 'respccid', 'ccid']:
                ret['HIDDEN_' + key] = value
            else:
                ret[key] = value
        if int(ret['HIDDEN_auth']) == 3 \
                and (int(ret['HIDDEN_respccid']) > 0 \
                or not ret['email'].endswith('@cern.ch')):
            ret['external'] = '1'
        else:
            ret['external'] = '0'
        return ret

