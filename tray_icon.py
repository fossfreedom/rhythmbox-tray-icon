#!/usr/bin/python
# coding=utf-8

from gi.repository import Gtk, Gdk, GdkPixbuf, Peas, GObject, RB
import os
import sys
import math

iconsPath = "/usr/share/icons/"
rhythmboxIcon = iconsPath + "hicolor/32x32/apps/rhythmbox.png"
playIcon = iconsPath + "gnome/32x32/actions/media-playback-start.png"

class TrayIcon(GObject.Object, Peas.Activatable):

    __gtype_name = 'TrayIcon'
    object = GObject.property(type=GObject.Object)

    starValue = 0
    iconsPath = "/usr/share/icons/"
    rhythmboxIcon = iconsPath + "hicolor/32x32/apps/rhythmbox.png"
    playIcon = os.path.join(sys.path[0], "tray_playing.png")
    menu = None


    def popup_menu(self, icon, button, time, data = None):
        """
        Called when the icon is right clicked, displays the menu
        """
        self.CreatePopupMenu()
        self.menu.popup(None, None, lambda w,x: self.icon.position_menu(self.menu, self.icon), self.icon, 3, time)

    def CreatePopupMenu(self):
        if not self.menu:
            self.SetMenuCss()

        self.menu = Gtk.Menu()

        playpause = Gtk.MenuItem("Play/Pause")
        next = Gtk.MenuItem("Next")
        prev = Gtk.MenuItem("Prev")
        quit = Gtk.MenuItem("Quit")

        starItem = self.GetRatingStar()
        if starItem:
           self.menu.append(starItem)

        playpause.connect("activate", self.play)
        next.connect("activate", self.nextItem)
        prev.connect("activate", self.previous)
        quit.connect("activate", self.quit)

        self.menu.append(playpause)
        self.menu.append(next)
        self.menu.append(prev)
        self.menu.append(quit)

        self.menu.show_all()

    def SetMenuCss(self):
        #Prevent background color when mouse hovers
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()

        #The only way I could do it: Re-set bg, border colors, causing menuitem to 'expand', then set the :hover colors with unico
        #Also strange, background-color is ignored, but background is not.
        css_provider.load_from_data("GtkMenuItem { border:@bg_color; background:@bg_color; } GtkMenuItem:hover { background:@selected_bg_color; } GtkWidget{ border: @bg_color; } #starMenu:hover { color:@fg_color;background: @bg_color; -unico-inner-stroke-width: 0; }")

        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


    def GetRatingStar(self):
        """ Gets a Gtk.MenuItem with the current song's ratings in filled stars """
        starItem = Gtk.MenuItem(self.GetStarsMarkup(0,5))
        self.starValue =  self.GetSongRating()
        label = starItem.get_children()[0]
        label.set_markup(self.GetStarsMarkup(self.starValue,5))

        starItem.set_name('starMenu')

        starItem.connect("motion_notify_event", self.OnStarMouseOver)
        starItem.connect("button_press_event", self.OnStarClick)
        starItem.connect("leave_notify_event", self.OnStarMouseOut)

        if self.starValue >= 0:
            return starItem
        else:
            return None

    def GetSongRating(self):
        """
        Gets the current song's user rating from Rhythmbox.
        """
        currentEntry = self.shell.props.shell_player.get_playing_entry()

        if currentEntry:
            return int(currentEntry.get_double(RB.RhythmDBPropType.RATING))
        else:
            return -1

    def OnStarClick(self, widget, event):
        """
        Method called when stars are clicked on. Determines chosen stars and sets song rating.
        """
        label = widget.get_children()[0]
        self.starValue = self.GetChosenStarsFromMousePosition(label, event.x)
        self.SetSongRating(self.starValue)

    def SetSongRating(self, rating):
        """
        Sets the current song rating in Rhythmbox.
        """
        currentEntry = self.shell.props.shell_player.get_playing_entry()
        self.db.entry_set(currentEntry, RB.RhythmDBPropType.RATING, rating)


    def GetChosenStarsFromMousePosition(self, label, mouseX):
        """
        Calculates the number of chosen stars to show based on the mouse's X position
        """
        starWidth = int(label.get_layout().get_pixel_size()[0]/5)
        chosen = math.ceil((mouseX-label.get_layout_offsets()[0])/starWidth)
        if chosen <= 0:
            chosen = 0

        if chosen >= 5:
            chosen = 5

        return chosen

    def OnStarMouseOut(self, widget, event):
        """
        Method called when mouse leaves the rating stars. Resets stars to original value.
        """
        label = widget.get_children()[0]
        label.set_markup(self.GetStarsMarkup(self.starValue, 5))


    def OnStarMouseOver(self, widget, event):
        """
        Method called when mouse hovers over the rating stars. Shows filled stars as mouse hovers.
        """
        label = widget.get_children()[0]
        label.set_markup(self.GetStarsMarkup(self.GetChosenStarsFromMousePosition(label,event.x), 5))

    def GetStarsMarkup(self, filledStars, totalStars):
        """
        Gets the Pango Markup for the star rating label
        """

        if filledStars is None or filledStars <= 0:
                    filledStars = 0

        if filledStars >= totalStars:
            filledStars = totalStars

        filledStars = int(math.ceil(filledStars))
        totalStars = int(totalStars)

        starString = '★' * filledStars + '☆' * (totalStars-filledStars)
        return "<span size='x-large' foreground='#000000'>" + starString + "</span>"

    def toggle(self, icon, event, data = None):
        if event.button == 1: # left button
            if self.wind.get_visible():
                self.wind.hide()
            else:
                self.wind.show()
                self.wind.present()

    def play(self, widget):
        self.player.playpause(True) # does nothing argument

    def nextItem(self, widget):
        self.player.do_next()

    def previous(self, widget):
        self.player.do_previous()

    def quit(self, widget):
        self.shell.quit()

    def hide_on_delete(self, widget, event):
        self.wind.hide()
        return True # don't actually delete

    def set_playing_icon(self, player, playing):
        if playing:
            self.icon.set_from_file(self.playIcon)
            currentEntry = self.shell.props.shell_player.get_playing_entry()
            self.icon.set_tooltip_text(currentEntry.get_string(RB.RhythmDBPropType.TITLE))
        else:
            self.icon.set_from_file(self.rhythmboxIcon)
            self.icon.set_tooltip_text("")

    def do_activate(self):
        self.shell = self.object
        self.wind = self.shell.get_property("window")
        self.player = self.shell.props.shell_player
        self.db = self.shell.props.db

        self.wind.connect("delete-event", self.hide_on_delete)
        self.CreatePopupMenu()

        self.icon =  Gtk.StatusIcon()
        self.icon.set_from_file(self.rhythmboxIcon)
        self.icon.connect("scroll-event", self.scroll)
        self.icon.connect("popup-menu", self.popup_menu)
        self.icon.connect("button-press-event", self.toggle)
        self.player.connect("playing-changed", self.set_playing_icon)

    def scroll(self, widget, event):
        vol = round(self.player.get_volume()[1],1)

        if event.direction == Gdk.ScrollDirection.UP:
            vol+=0.1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            vol-=0.1

        if vol <= 0:
            vol = 0

        if vol >=1:
            vol = 1

        self.player.set_volume(vol)


    def do_deactivate(self):
        self.icon.set_visible(False)
        del self.icon