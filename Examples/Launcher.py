"""
Hierarchy
KatanaLauncher --> (QWidget):
    |- layout (QVBoxLayout)
        |- launcher_args_view --> (ShojiLayout)
            |- katana_version --> LabelledInputWidget
            |- render_engine --> LabelledInputWidget
            |- render_version --> LabelledInputWidget
        |- plugins_view --> (MultiButtonInputWidget)
            |* buttons --> (ButtonInputWidget)
"""

import subprocess
import os
import sys

from qtpy.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout
from qtpy.QtCore import Qt

from cgwidgets.widgets import (
    ButtonInputWidgetContainer, ListInputWidget, LabelledInputWidget, ButtonInputWidget,
    ShojiLayout
)
from cgwidgets.settings.colors import iColor
from cgwidgets.utils import centerWidgetOnCursor


class KatanaLauncher(QWidget):
    '''
    Main Widget container the different options for launching Katana

    Attributes:
        default_katana_version (str)
        default_render_engine (str)
        default_render_version (str)
        katana_root (str): path to Katana root directory
        katana_dir (str): path to directory containing multiple Katana versions
        render_engine_dir (str): path to directory containing multiple render engines
        plugins (dict): dictionary of plugins to be installed
        envars (dict): of lists
            {envar:[value1, value2, value3]}
    '''
    def __init__(self, plugins=None):
        super(KatanaLauncher, self).__init__()
        # set defaults
        if not plugins:
            plugins = {}
        self._plugins = plugins

        self.default_katana_version = '5.0v1b1'
        self.default_render_engine = 'prman'
        self.default_render_engine_version = '24.1'

        self.katana_dir = '/opt/katana'
        self.render_engine_dir = '/opt/renderEngines'

        # create GUI
        self.__setupGUI()

        # setup style
        self.setStyleSheet(iColor.createDefaultStyleSheet(self))

    def __setupGUI(self):
        """
        Creates all of the widgets for the GUI
        """
        # setup basic args
        self.launcher_args_view = self.__setupBasicArgs()
        self.__populateBasicArgs()

        # create launcher button
        self.launch_katana_button = ButtonInputWidget(
            user_clicked_event=self.launchKatana, title="GO", flag=False, is_toggleable=False)
        self.launch_katana_button.setMinimumWidth(200)

        # setup plugins
        self.plugins_view = KatanaResourcesWidget(self)
        self.__setupPlugins(self._plugins)

        # setup defaults
        self.launcher_args_widgets['Katana'].setText(self.default_katana_version)
        self.launcher_args_widgets['Render Engine'].setText(self.default_render_engine)
        self.launcher_args_widgets['Render Version'].setText(self.default_render_engine_version)

        # setup args layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.launcher_args_view)
        main_layout.addWidget(self.plugins_view)

        # setup main layout
        QHBoxLayout(self)
        self.layout().addLayout(main_layout)
        self.layout().addWidget(self.launch_katana_button)

    def __setupBasicArgs(self):
        """
        Creates the basic launcher args widgets, this includes the

        Katana Version | Render Engine | Render Engine Version | Launcher Button

        Returns (ShojiLayout):

        """
        # create layout
        launcher_args_view = ShojiLayout(self)
        launcher_args_view.setOrientation(Qt.Horizontal)

        # create basic args widgets
        self.launcher_args_widgets = {}
        for option in ['Katana', "Render Engine", "Render Version"]:
            # create widget
            input_widget = LabelledInputWidget(name=option, delegate_widget=ListInputWidget(self))
            input_widget.delegateWidget().filter_results = False
            self.launcher_args_widgets[option] = input_widget.delegateWidget()
            self.launcher_args_widgets[option].setAlignment(Qt.AlignCenter)
            launcher_args_view.addWidget(input_widget)

            # set widget orientation
            input_widget.setDirection(Qt.Vertical)

        # create launcher button

        return launcher_args_view

    def __populateBasicArgs(self):
        """
        After the basic args widgets have been created.  This will setup
        all of the items available in each field, and connect the signals
        between the render versions.

        # connect user input
        input_widget.setUserFinishedEditingEvent(test)

        # list override
        if arg == "list":
            input_widget.delegateWidget().populate(list_of_crap)
            input_widget.delegateWidget().display_item_colors = True

        """
        # katana
        katana_versions = [[v] for v in sorted(os.listdir(self.katana_dir))]
        self.launcher_args_widgets['Katana'].populate(katana_versions)

        # render engine
        def updateRenderVersions(widget, render_engine):
            versions_dir = self.render_engine_dir + '/' + render_engine
            versions = [[v] for v in sorted(os.listdir(versions_dir))]
            self.launcher_args_widgets['Render Version'].populate(versions)

        render_engines = [[renderer] for renderer in sorted(os.listdir(self.render_engine_dir))]
        self.launcher_args_widgets['Render Engine'].populate(render_engines)
        self.launcher_args_widgets['Render Engine'].setUserFinishedEditingEvent(updateRenderVersions)

        updateRenderVersions(None, "prman")

    def __setupPlugins(self, plugins):
        self._plugins = plugins

        # Add Button
        for plugin in plugins:
            enabled = plugins[plugin]['__ENABLED__']
            self.plugins_view.addButton(plugin, plugin, enabled=enabled)

    """ SETUP PLUGINS """
    def installPlugins(self, katana_resources, envars):
        """
        Installs all of the plugins/envars needed to launch Katana

        Args:
            katana_resources (list): of strings containing Katana Resources directories
            envars (dict): of envars/values
                {'envar':'value', 'envar2', 'value2'}
        """
        # setup katana resources
        os.environ['KATANA_RESOURCES'] = self.katanaResources(katana_resources)

        # setup envars
        self._envars = self.envars(envars)
        for var in self._envars:
            os.environ[var] = self._envars[var].format(katana_root=self.katanaRoot())

    def plugins(self):
        return self._plugins

    def addPlugin(self, plugin):
        """
        Adds a plugin to the global plugin registry
        Args:
            plugin (dict):
                { name { resources: <PATH>, envars: {envar_name}
                {'USD':{
                    'resources':'{katana_root}/plugins/Resources/Usd/plugin'},
                    'envars': {'LD_LIBRARY_PATH':{'{katana_root/plugins/Resources/Usd/lib}'}}},

        Returns:
        """

    def katanaResources(self, resources=None):
        """
        Gets one big ass string to be used as the KATANA_RESOURCES envar

        Args:
            resources (list): of string paths to be append to the the KATANA_RESOURCES envar

        Returns (str): to set the KATANA_RESOURCES envar to
        """
        # create resources if non-existant
        if not resources:
            resources = []

        # user local resources
        resources.append('$HOME/.katana')

        # user selected resources from launcher
        for plugin in self.plugins_view.flags():
            resources.append(self.plugins()[plugin]['KATANA_RESOURCES'])
        #resources += (self.plugins_view.flags())

        # global resources
        if 'KATANA_RESOURCES' in os.environ:
            resources += os.environ['KATANA_RESOURCES'].split(':')

        # log katana resources
        self.katana_resources = resources

        return ':'.join(resources).format(katana_root=self.katanaRoot())

    def envars(self, envars=None):
        """
        Returns a dict of envars to be installed

        Args:
            envars (dict): of current envars
                {'envar': 'value1:value2:value3',
                'envar2': 'value1:value2:value3'}

        Returns (dict):
            {'envar': 'value1:value2:value3',
            'envar2': 'value1:value2:value3'}
        """
        # create default dict if none provided
        if not envars:
            envars = {}

        # setup envar values from flags selected
        for plugin in self.plugins_view.flags():
            for envar in self.plugins()[plugin].keys():
                if envar != "KATANA_RESOURCES":
                    if (not envar.startswith("__") and not envar.endswith("__")):
                        value = self.plugins()[plugin][envar]
                        if envar in envars.keys():
                            envars[envar] += ':' + value
                        else:
                            envars[envar] = value

        return envars

    """ UTILS """
    def katanaVersion(self):
        """
        Returns the current version of Katana
        Returns (str):
        """
        return self.launcher_args_widgets['Katana'].text()

    def katanaRoot(self):
        """
        Gets the root directory of the Katana install

        Returns (str):
        """
        katana_root = "{katana_dir}/{katana_version}".format(
            katana_dir=self.katana_dir,
            katana_version=self.katanaVersion())
        return katana_root

    def renderEngine(self):
        return self.launcher_args_widgets['Render Engine'].text()

    def renderVersion(self):
        return self.launcher_args_widgets['Render Version'].text()

    """ LAUNCH """
    def compileRenderEngine(self):
        resources = (self.render_engine_dir + '/' + self.renderEngine() + '/' + self.renderVersion())

        def arnold():
            envars = {
                'DEFAULT_RENDERER': 'arnold',
                'path': '%s/bin' % resources,
                'KTOA_ROOT': '%s' % resources,
            }
            return envars

        def delight():
            envars = {
                'DL_DISPLAYS_PATH': '%s/displays' % resources,
                'DL_SHADERS_PATH': '%s/shaders' % resources,
                'DEFAULT_RENDERER': 'dl',
                'DLFK_INSTALL_PATH': '%s/3DelightForKatana' % resources,
                'LD_LIBRARY_PATH': '%s/lib' % resources,
                'DELIGHT': resources
            }
            return envars

        def prman():
            envars = {
                'RMANTREE': '%s/PROSERVER' % resources,
                'DEFAULT_RENDERER': 'prman',
                'PIXAR_LICENSE_FILE': '/opt/renderEngines/prman/24.1/pixar.license'
            }
            return envars

        def redshift():
            """
            export LD_LIBRARY_PATH="/usr/redshift/bin:${LD_LIBRARY_PATH}"
            export KATANA_RESOURCES=/usr/redshift/redshift4katana/katana2.5v4
            export DEFAULT_RENDERER=Redshift
            Returns:

            """
            LD_LIBRARY_PATH = "%s/bin" % resources
            envars = {
                "LD_LIBRARY_PATH":LD_LIBRARY_PATH
            }
            # envars = {
            #     'KATANA_HOME': '%s/Katana3.0v1' % self.katana_dir,
            #     'REDSHIFT_HOME': '%s/bin' % resources,
            #     'DEFAULT_RENDERER': 'Redshift',
            #     'KATANA_VERSION': '3.0v1',
            #     'REDSHIFT4KATANA_HOME': '%s/Plugins/Katana/3.0v1' % resources,
            #     'path': '%s/bin' % resources,
            # }
            return envars

        def vray():
            envars = {
                'VRAY_FOR_KATANA_PLUGINS_x64': '%s/vrayplugins' % resources,
                'path': '%s/RenderBin' % resources,
                'DEFAULT_RENDERER': 'vray'
            }
            return envars

        # Choose which render engine to use
        if self.renderEngine() == 'delight':
            katana_resources = ['%s/3DelightForKatana' % resources]
            envars = delight()
        elif self.renderEngine() == 'arnold':
            katana_resources = ['%s' % resources]
            envars = arnold()
        elif self.renderEngine() == 'vray':
            katana_resources = ['%s' % resources]
            envars = vray()
        elif self.renderEngine() == 'prman':
            katana_resources = ['%s/RFK/plugins/Resources/PRMan' % resources]
            envars = prman()
        elif self.renderEngine() == 'redshift':
            katana_resources = ['%s/redshift4katana/katana4.0v1' % resources]
            envars = redshift()

        # return dicts
        return katana_resources, envars

    def launchKatana(self, widget):
        '''
        Instantiate Katana, this will read all of the inputs that the user has selected
        and launch Katana with the correct environment
        '''
        # path to render engine

        self.katana_bin = self.katanaRoot() + '/katana'
        katana_resources, envars = self.compileRenderEngine()

        # set env variables
        self.installPlugins(katana_resources, envars)

        # image library directory
        # os.environ['LIBRARY_DIR'] = '/media/ssd01/library/library'

        # display launcher text
        self.launcherText()

        # TODO Move this to a dynamic module
        # image library directory
        os.environ['LIBRARY_DIR'] = '/media/ssd01/library/library'

        # additional 2.7 libs
        os.environ["PYTHONPATH"] += ":/usr/local/lib/python2.7/dist-packages"
        # # launch katana instance
        subprocess.Popen([self.katana_bin])
        self.close()

    def launcherText(self):
        """
        Nasty ass print statement because Im to lazy to set up proper logging
        """
        print("""
...............................................................................
..............................      LOADING      ..............................
...............................................................................
\t\t\t ___   ____    __  __    ___    ___    ___ 
\t\t\t| __| |_  /   |  \/  |  / _ \  |   \  | __|
\t\t\t| _|   / /    | |\/| | | (_) | | |) | | _| 
\t\t\t|___| /___|   |_|  |_|  \___/  |___/  |___|
                                    
...............................................................................
..........................      THE EASY STUFF      ...........................
...............................................................................""")
        print("\t|__  Loading Katana Resources... ")
        for path in self.katana_resources:
            print ("\t|\t|__  ", path.format(katana_root=self.katanaRoot()))

        # setup envars
        print('')
        print("\t|__  Setting Environment Variables")
        for var in self._envars:
            print('\t|\t|__  {envar}   ==>  {value}'.format(
                envar=var,
                value=self._envars[var].format(katana_root=self.katanaRoot())
            ))

        """ EVENTS """

    def keyPressEvent(self, event, *args, **kwargs):
        if (
            event.key() == Qt.Key_Enter
            or event.key() == Qt.Key_Return
        ):
            self.launchKatana(self)
        return QWidget.keyPressEvent(self, event, *args, **kwargs)


class KatanaResourcesWidget(ButtonInputWidgetContainer):
    """
    Widget that contains flags for enabling/disabling 3rd party plugins.
    """
    def __init__(self, parent=None):
        super(KatanaResourcesWidget, self).__init__(parent)

    def addResourcesDirectory(self, name, path, enabled=True):
        """
        Creates a button that will display the ability to toggle on/off the resource directory for the user

        Args:
            name (str): to be displayed to the user
            path (str): location on disk of Katana Resources directory
        """
        button = self.addButton(name, path)
        self.setButtonAsCurrent(button, enabled=enabled)

    def showEvent(self, event):
        """
        Normalize widget sizes
        """

        ButtonInputWidgetContainer.showEvent(self, event)
        self.normalizeWidgetSizes()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    plugins = {
        'Foundry': {
            'KATANA_RESOURCES':'/media/ssd01/dev/katana/KatanaResources_foundry/',
            '__ENABLED__': False},
        'Katana Widgets': {
            'KATANA_RESOURCES': '/media/ssd01/dev/katana/KatanaWidgets',
            '__ENABLED__': True},
        'USD': {
            'KATANA_RESOURCES': '{katana_root}/plugins/Resources/Usd/plugin',
            'LD_LIBRARY_PATH': '{katana_root}/plugins/Resources/Usd/lib',
            '__ENABLED__': True},
        'Katana Examples': {
            'KATANA_RESOURCES': '{katana_root}/plugins/Src/Resources/Examples',
            '__ENABLED__': False},
        'Old Crap': {
            'KATANA_RESOURCES': '/media/ssd01/dev/katana/KatanaResources_old/',
            '__ENABLED__': False}
    }

    # create main application
    launcher = KatanaLauncher(plugins=plugins)

    # force widget on top
    launcher.setWindowFlag(Qt.WindowStaysOnTopHint)
    launcher.setWindowState(launcher.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    launcher.activateWindow()

    # show widget
    launcher.show()
    launcher.resize(1000, 250)
    centerWidgetOnCursor(launcher)

    sys.exit(app.exec_())
