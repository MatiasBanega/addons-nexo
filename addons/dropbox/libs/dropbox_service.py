# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

try:
    from dropbox import Dropbox, DropboxTeam, DropboxOAuth2Flow
    from dropbox.sharing import RequestedVisibility, SharedLinkSettings
except ImportError as e:
    _logger.error(e)
    Dropbox = object
    DropboxTeam = object
    DropboxOAuth2Flow = object


class Client(Dropbox):
    """
    The class to apply for Dropbox objects and methods
    """
    def files_list_folder_d(self,
                            path,
                            recursive=False,
                            include_media_info=False,
                            include_deleted=False,
                            include_has_explicit_shared_members=False,
                            include_mounted_folders=True,
                            limit=None,
                            shared_link=None,
                            include_property_groups=None):
        """
        Re-write to get not 2000 items, but all of them
        """
        res = self.files_list_folder(path=path, recursive=recursive, include_media_info=include_media_info,
                                    include_deleted=include_deleted,
                                    include_has_explicit_shared_members=include_has_explicit_shared_members,
                                    include_mounted_folders=True, limit=limit,
                                    shared_link=shared_link, include_property_groups=include_property_groups)
        entries = res.entries
        while res.has_more:
            res = self.files_list_folder_continue(cursor=res.cursor)
            entries += res.entries
        return entries

    def get_team_link_d(self, path, team):
        """
        The method to generate team link
         1. Try to retrieve existing link. We get only 'direct' links, since otherwise link would be for some
            parent folder
         2. Try to genereate 'team_only' link. Basic Dropbox users do not have rights for such links
         3. Make public link

        Args:
         * path - char -Dropbox path
         * team - bool - whether it is a team account

        Returns:
         * url - char
        """
        # 1
        existing_links = self.sharing_list_shared_links(path, direct_only=True).links
        if existing_links:
            url = existing_links[0].url
        else:
            if team:
                # 2
                rq_visibility = RequestedVisibility(u'team_only')
                url = self.sharing_create_shared_link_with_settings(
                    path=path,
                    settings=SharedLinkSettings(requested_visibility=rq_visibility)
                ).url
            else:
                # 3
                url = self.sharing_create_shared_link_with_settings(path=path).url
        return url

class ClientTeam(DropboxTeam):
    """
    The class to apply for Dropbox objects and methods under Team API
    """
    def _get_dropbox_client_with_select_header(self, select_header_name, team_member_id):
        """
        Overwrite to use the Client, not just DropBox
        """
        new_headers = self._headers.copy() if self._headers else {}
        new_headers[select_header_name] = team_member_id
        return Client(
            self._oauth2_access_token,
            max_retries_on_error=self._max_retries_on_error,
            max_retries_on_rate_limit=self._max_retries_on_rate_limit,
            timeout=self._timeout,
            user_agent=self._raw_user_agent,
            session=self._session,
            headers=new_headers,
        )
