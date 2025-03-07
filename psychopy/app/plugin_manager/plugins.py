import wx
from wx.lib import scrolledpanel
import webbrowser
from PIL import Image as pil

from .utils import uninstallPackage, installPackage
from psychopy.tools import pkgtools
from psychopy.app.themes import theme, handlers, colors, icons
from psychopy.app import utils
from psychopy.localization import _translate
from psychopy import plugins
import subprocess as sp
import sys
import requests


class AuthorInfo:
    """Plugin author information.

    Parameters
    ----------
    name : str
        Author name.
    email : str
        Author email URL.
    github : str
        GitHub repo URL (optional).
    avatar : str
        Avatar image file or URL.

    """
    def __init__(self,
                 name="",
                 email="",
                 github="",
                 avatar=None):
        self.name = name
        self.email = email
        self.github = github
        self.avatar = avatar

    def __eq__(self, other):
        if other == "ost":
            # If author is us, check against our github
            return self.github == "psychopy"
        else:
            # Otherwise check against string attributes
            return other in (self.name, self.email, self.github)

    @property
    def avatar(self):
        if hasattr(self, "_avatar"):
            return self._avatar

    @avatar.setter
    def avatar(self, value):
        self._requestedAvatar = value
        self._avatar = utils.ImageData(value)

    def __repr__(self):
        return (f"<psychopy.app.plugins.AuthorInfo: "
                f"{self.name} (@{self.github}, {self.email})>")


class PluginInfo:
    """Minimal class to store info about a plugin.

    Parameters
    ----------
    pipname : str
        Name of plugin on pip, e.g. "psychopy-legacy".
    name : str
        Plugin name for display, e.g. "Psychopy Legacy".
    icon : wx.Bitmap, path or None
        Icon for the plugin, if any (if None, will use blank bitmap).
    description : str
        Description of the plugin.
    installed : bool or None
        Whether or not the plugin in installed on this system.
    active : bool
        Whether or not the plug is enabled on this system (if not installed,
        will always be False).

    """

    def __init__(self,
                 pipname, name="",
                 author=None, homepage="", docs="", repo="",
                 keywords=None,
                 icon=None, description=""):
        self.pipname = pipname
        self.name = name
        self.author = author
        self.homepage = homepage
        self.docs = docs
        self.repo = repo
        self.icon = icon
        self.description = description
        self.keywords = keywords or []

    def __repr__(self):
        return (f"<psychopy.plugins.PluginInfo: {self.name} "
                f"[{self.pipname}] by {self.author}>")

    def __eq__(self, other):
        if isinstance(other, PluginInfo):
            return self.pipname == other.pipname
        else:
            return self.pipname == str(other)

    @property
    def icon(self):
        if hasattr(self, "_icon"):
            return self._icon

    @icon.setter
    def icon(self, value):
        self._requestedIcon = value
        self._icon = utils.ImageData(value)

    @property
    def active(self):
        """
        Is this plugin active? If so, it is loaded when the app starts.
        Otherwise, it remains installed but is not loaded.
        """
        return plugins.isStartUpPlugin(self.pipname)

    @active.setter
    def active(self, value):
        if value is None:
            # Setting active as None skips the whole process - useful for
            # avoiding recursion
            return

        if value:
            # If active, add to list of startup plugins
            plugins.startUpPlugins(self.pipname, add=True)
        else:
            # If active and changed to inactive, remove from list of startup
            # plugins.
            current = plugins.listPlugins(which='startup')
            if self.pipname in current:
                current.remove(self.pipname)
            plugins.startUpPlugins(current, add=False)

    def activate(self, evt=None):
        self.active = True

    def deactivate(self, evt=None):
        self.active = False

    def install(self):
        installPackage(self.pipname)
        plugins.scanPlugins()

    def uninstall(self):
        uninstallPackage(self.pipname)
        plugins.scanPlugins()
        pass

    @property
    def installed(self):
        return pkgtools.isInstalled(self.pipname)

    @installed.setter
    def installed(self, value):
        if value is None:
            # Setting installed as None skips the whole process - useful for
            # avoiding recursion
            return
        # Get action string from value
        if value and not self.installed:
            self.install()
        elif self.installed:
            self.uninstall()

    @property
    def author(self):
        if hasattr(self, "_author"):
            return self._author

    @author.setter
    def author(self, value):
        if isinstance(value, AuthorInfo):
            # If given an AuthorInfo, use it directly
            self._author = value
        elif isinstance(value, dict):
            # If given a dict, make an AuthorInfo from it
            self._author = AuthorInfo(**value)
        else:
            # Otherwise, assume no author
            self._author = AuthorInfo()


class PluginManagerPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Make splitter
        self.splitter = wx.SplitterWindow(self)
        self.sizer.Add(self.splitter, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # Make list
        self.pluginList = PluginBrowserList(self.splitter)
        # Make viewer
        self.pluginViewer = PluginDetailsPanel(self.splitter)
        # Cross-reference viewer & list
        self.pluginViewer.list = self.pluginList
        self.pluginList.viewer = self.pluginViewer
        # Assign to splitter
        self.splitter.SplitVertically(
            window1=self.pluginList,
            window2=self.pluginViewer,
            sashPosition=0
        )
        self.splitter.SetMinimumPaneSize(450)
        # Mark installed on items now that we have necessary references
        for item in self.pluginList.items:
            item.markInstalled(item.info.installed)
        # Start of with nothing selected
        self.pluginList.onDeselect()

        self.Layout()
        self.theme = theme.app

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour("white")
        # Manually style children as Splitter interfered with inheritance
        self.pluginList.theme = self.theme
        self.pluginViewer.theme = self.theme


class PluginBrowserList(scrolledpanel.ScrolledPanel, handlers.ThemeMixin):
    class PluginListItem(wx.Window, handlers.ThemeMixin):
        """
        Individual item pointing to a plugin
        """
        def __init__(self, parent, info):
            wx.Window.__init__(self, parent=parent, style=wx.SIMPLE_BORDER)
            self.SetMaxSize((400, -1))
            self.parent = parent
            # Link info object
            self.info = info
            # Setup sizer
            self.border = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.border)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
            # Add label
            self.label = wx.BoxSizer(wx.VERTICAL)
            self.nameLbl = wx.StaticText(self, label=info.name)
            self.label.Add(self.nameLbl, flag=wx.ALIGN_LEFT)
            self.pipNameLbl = wx.StaticText(self, label=info.pipname)
            self.label.Add(self.pipNameLbl, flag=wx.ALIGN_LEFT)
            self.sizer.Add(self.label, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)
            # Button sizer
            self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer.Add(self.btnSizer, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
            # Add install button
            self.installBtn = PluginInstallBtn(self)
            self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
            self.btnSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)

            # Map to onclick function
            self.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            self.nameLbl.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            self.pipNameLbl.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            # Bind navigation
            self.Bind(wx.EVT_NAVIGATION_KEY, self.onNavigation)

            self._applyAppTheme()

        def _applyAppTheme(self):
            # Set label fonts
            from psychopy.app.themes import fonts
            self.nameLbl.SetFont(fonts.appTheme['h6'].obj)
            self.pipNameLbl.SetFont(fonts.coderTheme.base.obj)
            # Mark installed/active
            self.markInstalled(self.info.installed)
            self.markActive(self.info.active)

        def onNavigation(self, evt=None):
            """
            Use the tab key to progress to the next panel, or the arrow keys to
            change selection in this panel.

            This is the same functionality as in a wx.ListCtrl
            """
            # Some shorthands for prev, next and whether each have focus
            prev = self.GetPrevSibling()
            prevFocus = False
            if hasattr(prev, "HasFocus"):
                prevFocus = prev.HasFocus()
            next = self.GetNextSibling()
            nextFocus = False
            if hasattr(next, "HasFocus"):
                nextFocus = next.HasFocus()

            if evt.GetDirection() and prevFocus:
                # If moving forwards from previous sibling, target is self
                target = self
            elif evt.GetDirection() and self.HasFocus():
                # If moving forwards from self, target is next sibling
                target = next
            elif evt.GetDirection():
                # If we're moving forwards from anything else, this event shouldn't have happened. Just deselect.
                target = None
            elif not evt.GetDirection() and nextFocus:
                # If moving backwards from next sibling, target is self
                target = self
            elif not evt.GetDirection() and self.HasFocus():
                # If moving backwards from self, target is prev sibling
                target = prev
            else:
                # If we're moving backwards from anything else, this event shouldn't have happened. Just deselect.
                target = None

            # If target is self or another PluginListItem, select it
            if target in self.parent.items:
                self.parent.setSelection(target)
                target.SetFocus()
            else:
                self.parent.setSelection(None)

            # Do usual behaviour
            evt.Skip()

        def onSelect(self, evt=None):
            self.parent.setSelection(self)

        def onInstall(self, evt=None):
            # Mark pending
            self.markInstalled(None)
            # Install
            self.info.install()
            # Mark installed
            self.markInstalled(self.info.installed)

        def markInstalled(self, installed=True):
            """
            Shorthand to call markInstalled with self and corresponding item

            Parameters
            ----------
            installed : bool or None
                True if installed, False if not installed, None if pending/unclear
            """
            markInstalled(
                pluginItem=self,
                pluginPanel=self.parent.viewer,
                installed=installed
            )

        def markActive(self, active=True):
            """
            Visually indicate that this item is either active or inactive

            Parameters
            ----------
            active : bool
                True if active, False if inactive
            """

            # Get text color according to active status
            if active:
                col = colors.app.light['text']
            else:
                col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
            # Style text
            self.nameLbl.SetForegroundColour(col)
            self.pipNameLbl.SetForegroundColour(col)
            self.Refresh()


    def __init__(self, parent, viewer=None):
        scrolledpanel.ScrolledPanel.__init__(self, parent=parent, style=wx.VSCROLL)
        self.parent = parent
        self.viewer = viewer
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Add search box
        self.searchCtrl = wx.SearchCtrl(self)
        self.sizer.Add(self.searchCtrl, border=9, flag=wx.ALL | wx.EXPAND)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.search)
        # Setup items sizers & labels
        self.itemSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.itemSizer, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)

        # Bind deselect
        self.Bind(wx.EVT_LEFT_DOWN, self.onDeselect)

        # Setup items
        self.items = []
        self.populate()
        # Store state of plugins on init so we can detect changes later
        self.initState = {}
        for item in self.items:
            self.initState[item.info.pipname] = {"installed": item.info.installed, "active": item.info.active}

    def populate(self):
        for item in self.items:
            self.removeItem(item)
        # Get all plugin details
        items = getAllPluginDetails()
        # Put installed packages at top of list
        items.sort(key=lambda obj: obj.installed, reverse=True)
        for item in items:
            self.appendItem(item)
        # Layout
        self.Layout()
        self.SetupScrolling()

    def search(self, evt=None):
        searchTerm = self.searchCtrl.GetValue().strip()
        for item in self.items:
            # Otherwise show/hide according to search
            match = any((
                searchTerm == "",  # If search is blank, show all
                searchTerm.lower() in item.info.name.lower(),
                searchTerm.lower() in item.info.pipname.lower(),
                searchTerm.lower() in [val.lower() for val in item.info.keywords],
                searchTerm.lower() in item.info.author.name.lower(),
            ))
            item.Show(match)

        self.Layout()

    def getChanges(self):
        """
        Check what plugins have changed state (installed, active) since this dialog was opened
        """
        changes = {}
        for item in self.items:
            info = item.info
            # Skip if its init state wasn't stored
            if info.pipname not in self.initState:
                continue
            # Get inits
            inits = self.initState[info.pipname]

            itemChanges = []
            # Has it been activated?
            if info.active and not inits['active']:
                itemChanges.append("activated")
            # Has it been deactivated?
            if inits['active'] and not info.active:
                itemChanges.append("deactivated")
            # Has it been installed?
            if info.installed and not inits['installed']:
                itemChanges.append("installed")

            # Add changes if there are any
            if itemChanges:
                changes[info.pipname] = itemChanges

        return changes

    def onClick(self, evt=None):
        self.SetFocusIgnoringChildren()
        self.viewer.info = None

    def setSelection(self, item):
        """
        Set the current selection as either None or the handle of a PluginListItem
        """
        if item is None:
            # If None, set to no selection
            self.selected = None
            self.viewer.info = None
        elif isinstance(item, self.PluginListItem):
            # If given a valid item, select it
            self.selected = item
            self.viewer.info = item.info
        # Style all items
        for obj in self.items:
            if obj == self.selected:
                # Selected colors
                bg = colors.app.light['panel_bg']
            else:
                # Deselected colors
                bg = colors.app.light['tab_bg']
            # Set color
            obj.SetBackgroundColour(bg)
            # Restyle item
            obj._applyAppTheme()
            # Refresh
            obj.Update()
            obj.Refresh()

        # Post CHOICE event
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId)
        evt.SetEventObject(self)
        evt.SetClientData(item)
        wx.PostEvent(self, evt)

    def onDeselect(self, evt=None):
        """
        If panel itself (not any children) are clicked on, set selection to None
        """
        self.setSelection(None)

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour("white")

    def appendItem(self, info):
        item = self.PluginListItem(self, info)
        self.items.append(item)
        self.itemSizer.Add(item, border=6, flag=wx.ALL | wx.EXPAND)

    def getItem(self, info):
        """
        Get the PluginListItem object associated with a PluginInfo object
        """
        for item in self.items:
            if item.info == info:
                return item


class PluginDetailsPanel(wx.Panel, handlers.ThemeMixin):
    iconSize = (128, 128)

    def __init__(self, parent, info=None, list=None):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.list = list
        # Setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.headSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headSizer, flag=wx.EXPAND)
        # Icon ctrl
        self.icon = wx.StaticBitmap(self, bitmap=wx.Bitmap(), size=self.iconSize, style=wx.SIMPLE_BORDER)
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL | wx.EXPAND)
        # Title
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.title = wx.StaticText(self, label="...")
        self.titleSizer.Add(self.title, flag=wx.EXPAND)
        # Pip name
        self.pipName = wx.StaticText(self, label="psychopy-...")
        self.titleSizer.Add(self.pipName, flag=wx.EXPAND)
        # Buttons
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.AddStretchSpacer()
        self.titleSizer.Add(self.buttonSizer, flag=wx.EXPAND)
        self.installBtn = PluginInstallBtn(self)
        self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
        self.buttonSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.EXPAND)
        self.activeBtn = wx.ToggleButton(self)
        self.activeBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onActivate)
        self.buttonSizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Description
        self.description = utils.MarkdownCtrl(
            self, value="",
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL
        )
        self.sizer.Add(self.description, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)
        # Keywords
        self.keywordsCtrl = utils.ButtonArray(
            self,
            orient=wx.HORIZONTAL,
            itemAlias=_translate("keyword"),
            readonly=True
        )
        self.sizer.Add(self.keywordsCtrl, border=6, flag=wx.ALL | wx.EXPAND)

        self.sizer.Add(wx.StaticLine(self), border=6, flag=wx.EXPAND | wx.ALL)

        # Add author panel
        self.author = AuthorDetailsPanel(self, info=None)
        self.sizer.Add(self.author, border=6, flag=wx.EXPAND | wx.ALL)

        self.info = info
        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        # Set background
        self.SetBackgroundColour("white")
        self.keywordsCtrl.SetBackgroundColour("white")
        # Set fonts
        from psychopy.app.themes import fonts
        self.title.SetFont(fonts.appTheme['h1'].obj)
        self.pipName.SetFont(fonts.coderTheme.base.obj)

    def markInstalled(self, installed=True):
        """
        Shorthand to call markInstalled with self and corresponding item

        Parameters
        ----------
        installed : bool or None
            True if installed, False if not installed, None if pending/unclear
        """
        if self.list:
            item = self.list.getItem(self.info)
        else:
            item = None
        markInstalled(
            pluginItem=item,
            pluginPanel=self,
            installed=installed
        )

    def markActive(self, active=True):
        """
        Visually indicate that this item is either active or inactive

        Parameters
        ----------
        active : bool
            True if active, False if inactive
        """
        self.activeBtn.SetValue(active)
        # Update button label
        if active:
            self.activeBtn.SetLabelText(_translate("Enabled"))
        else:
            self.activeBtn.SetLabelText(_translate("Disabled"))
        # Style list item
        if self.list:
            item = self.list.getItem(self.info)
            if item is not None:
                item.markActive(active)

    def onInstall(self, evt=None):
        # Mark as pending
        self.markInstalled(installed=None)
        # Do install
        self.info.install()
        # Mark according to install success
        self.markInstalled(self.info.installed)

    def onActivate(self, evt=None):
        active = self.activeBtn.GetValue()
        # Activate plugin
        if active:
            self.info.activate()
        else:
            self.info.deactivate()
        # Visually update to show active status
        self.markActive(active)


    @property
    def info(self):
        """
        Information about this plugin
        """
        return self._info

    @info.setter
    def info(self, value):
        self.Enable(value is not None)
        # Handle None
        if value is None:
            value = PluginInfo(
                "psychopy-...",
                name="..."
            )
        self._info = value
        # Set icon
        icon = value.icon
        if icon is None:
            icon = wx.Bitmap()
        if isinstance(icon, pil.Image):
            # Resize to fit ctrl
            icon = icon.resize(size=self.iconSize)
            # Supply an alpha channel if there is one
            if "A" in icon.getbands():
                alpha = icon.tobytes("raw", "A")
            else:
                alpha = None
            icon = wx.Bitmap.FromBufferAndAlpha(
                width=icon.size[0],
                height=icon.size[1],
                data=icon.tobytes("raw", "RGB"),
                alpha=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.icon.SetBitmap(icon)
        # Set names
        self.title.SetLabelText(value.name)
        self.pipName.SetLabelText(value.pipname)
        # Set installed
        self.markInstalled(value.installed)
        # Set activated
        self.markActive(value.active)
        # Set description
        self.description.setValue(value.description)
        # Set keywords
        self.keywordsCtrl.items = value.keywords

        # Set author info
        self.author.info = value.author

        self.Layout()


class AuthorDetailsPanel(wx.Panel, handlers.ThemeMixin):
    avatarSize = (64, 64)

    def __init__(self, parent, info):
        wx.Panel.__init__(self, parent)

        # Setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Details sizer
        self.detailsSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.detailsSizer, proportion=1, border=6, flag=wx.LEFT | wx.EXPAND)
        # Name
        self.name = wx.StaticText(self)
        self.detailsSizer.Add(self.name, border=6, flag=wx.ALIGN_RIGHT | wx.ALL)

        # Button sizer
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detailsSizer.Add(self.buttonSizer, border=3, flag=wx.ALIGN_RIGHT | wx.ALL)
        # Email button
        self.emailBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.emailBtn.SetToolTip(_translate("Email author"))
        self.emailBtn.Bind(wx.EVT_BUTTON, self.onEmailBtn)
        self.buttonSizer.Add(self.emailBtn, border=3, flag=wx.EXPAND | wx.ALL)
        # GitHub button
        self.githubBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.githubBtn.SetToolTip(_translate("Author's GitHub"))
        self.githubBtn.Bind(wx.EVT_BUTTON, self.onGithubBtn)
        self.buttonSizer.Add(self.githubBtn, border=3, flag=wx.EXPAND | wx.ALL)

        # Avatar
        self.avatar = wx.StaticBitmap(self, bitmap=wx.Bitmap(), size=self.avatarSize, style=wx.BORDER_NONE)
        self.sizer.Add(self.avatar, border=6, flag=wx.ALL | wx.EXPAND)

        # Set initial info
        if info is not None:
            self.info = info

        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        # Name font
        from psychopy.app.themes import fonts
        self.name.SetFont(fonts.appTheme['h4'].obj)
        # Email button bitmap
        self.emailBtn.SetBitmap(icons.ButtonIcon("email", 16).bitmap)
        self.emailBtn.SetBitmapDisabled(icons.ButtonIcon("email", 16).bitmap)
        # Github button bitmap
        self.githubBtn.SetBitmap(icons.ButtonIcon("github", 16).bitmap)
        self.githubBtn.SetBitmapDisabled(icons.ButtonIcon("github", 16).bitmap)

    @property
    def info(self):
        if hasattr(self, "_info"):
            return self._info

    @info.setter
    def info(self, value):
        # Alias None
        if value is None:
            value = AuthorInfo(
                name="..."
            )
        # Store value
        self._info = value
        # Update avatar
        icon = value.avatar
        if icon is None:
            icon = wx.Bitmap()
        if isinstance(icon, pil.Image):
            # Resize to fit ctrl
            icon = icon.resize(size=self.avatarSize)
            # Supply an alpha channel
            if "A" not in icon.getbands():
                # Make sure there's an alpha channel to supply
                alpha = pil.new("L", icon.size, 255)
                icon.putalpha(alpha)
            alpha = icon.tobytes("raw", "A")

            icon = wx.Bitmap.FromBufferAndAlpha(
                width=icon.size[0],
                height=icon.size[1],
                data=icon.tobytes("raw", "RGB"),
                alpha=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.avatar.SetBitmap(icon)
        # Update name
        self.name.SetLabelText(value.name)
        # Add tooltip for OST
        if value == "ost":
            self.name.SetToolTip(_translate(
                "That's us! We make PsychoPy and Pavlovia!"
            ))
        else:
            self.name.SetToolTip("")
        # Show/hide buttons
        self.emailBtn.Show(bool(value.email))
        self.githubBtn.Show(bool(value.github))

    def onEmailBtn(self, evt=None):
        webbrowser.open(f"mailto:{self.info.email}")

    def onGithubBtn(self, evt=None):
        webbrowser.open(f"github.com/{self.info.github}")


class PluginInstallBtn(wx.Button, handlers.ThemeMixin):
    """
    Install button for a plugin, comes with a method to update its appearance according to installation
    status & availability
    """
    def __init__(self, parent):
        # Initialise
        wx.Button.__init__(
            self, parent,
            label="..."
        )
        self.SetBitmap(icons.ButtonIcon("download", 16).bitmap)

    def markInstalled(self, installed=True):
        """
        Mark on this button whether install has completed / is in progress / is available

        Parameters
        ----------
        installed : bool or None
            True if installed, False if not installed, None if pending/unclear
        """
        if installed is None:
            # If pending, disable and set label as ellipsis
            self.Disable()
            self.SetLabelText("...")
            self.setAllBitmaps(icons.ButtonIcon("view-refresh", 16).bitmap)
        elif installed:
            # If installed, disable and set label as installed
            self.Disable()
            self.SetLabelText(_translate("Installed"))
            self.setAllBitmaps(icons.ButtonIcon("greytick", 16).bitmap)
        else:
            # If not installed, enable and set label as not installed
            self.Enable()
            self.SetLabelText(_translate("Install"))
            self.setAllBitmaps(icons.ButtonIcon("download", 16).bitmap)

        self.Refresh()

    def setAllBitmaps(self, bmp):
        self.SetBitmap(bmp)
        self.SetBitmapDisabled(bmp)
        self.SetBitmapPressed(bmp)
        self.SetBitmapCurrent(bmp)

    def _applyAppTheme(self):
        # Setup icon
        self.SetBitmapMargins(6, 3)


def markInstalled(pluginItem, pluginPanel, installed=True):
    """
    Setup installed button according to install state

    Parameters
    ----------
    pluginItem : PluginBrowserList.PluginListItem
        Plugin list item associated with this plugin
    pluginPanel : PluginDetailsPanel
        Plugin viewer panel to update
    installed : bool or None
        True if installed, False if not installed, None if pending/unclear
    """
    # Update plugin item
    if pluginItem:
        pluginItem.installBtn.markInstalled(installed)
    # Update panel (if applicable)
    if pluginPanel and pluginItem and pluginPanel.info == pluginItem.info:
        pluginPanel.installBtn.markInstalled(installed)
        pluginPanel.activeBtn.Enable(bool(installed))


def markActive(pluginItem, pluginPanel, installed=True):
    """
    Setup installed button according to install state

    Parameters
    ----------
    pluginItem : PluginBrowserList.PluginListItem
        Plugin list item associated with this plugin
    pluginPanel : PluginDetailsPanel
        Plugin viewer panel to update
    installed : bool or None
        True if installed, False if not installed, None if pending/unclear
    """



def getAllPluginDetails():
    """
    Placeholder function - returns an example list of objects with desired
    structure.
    """
    # Request plugin info list from server
    resp = requests.get("https://psychopy.org/plugins.json")
    # If 404, return None so the interface can handle this nicely rather than an
    # unhandled error.
    if resp.status_code == 404:
        return

    # Create PluginInfo objects from info list
    objs = []
    for info in resp.json():
        objs.append(
            PluginInfo(**info)
        )

    # Add info objects for local plugins which aren't found online
    localPlugins = plugins.listPlugins(which='all')
    for name in localPlugins:
        # Check whether plugin is accounted for
        if name not in objs:
            # If not, get its metadata
            data = plugins.pluginMetadata(name)
            # Create best representation we can from metadata
            author = AuthorInfo(
                name=data.get('Author', ''),
                email=data.get('Author-email', ''),
            )
            info = PluginInfo(
                pipname=name, name=name,
                author=author,
                homepage=data.get('Home-page', ''),
                keywords=data.get('Keywords', ''),
                description=data.get('Summary', ''),
            )
            # Add to list
            objs.append(info)

    return objs


if __name__ == "__main__":
    pass



