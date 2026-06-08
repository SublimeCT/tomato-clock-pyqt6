from __future__ import annotations

import ctypes
from ctypes import c_bool, c_char_p, c_double, c_size_t, c_ubyte, c_ulong, c_void_p
from typing import Callable


class NSSize(ctypes.Structure):
    _fields_ = [("width", c_double), ("height", c_double)]


class MacStatusItem:
    def __init__(self):
        self._objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        self._appkit = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")

        self._objc.objc_getClass.restype = c_void_p
        self._objc.objc_getClass.argtypes = [c_char_p]
        self._objc.sel_registerName.restype = c_void_p
        self._objc.sel_registerName.argtypes = [c_char_p]

        self._msg_send_0 = self._make_msg_send(c_void_p, [c_void_p, c_void_p])
        self._msg_send_1p = self._make_msg_send(c_void_p, [c_void_p, c_void_p, c_void_p])
        self._msg_send_1d = self._make_msg_send(c_void_p, [c_void_p, c_void_p, c_double])
        self._msg_send_1b_void = self._make_msg_send(None, [c_void_p, c_void_p, c_bool])
        self._msg_send_1u_void = self._make_msg_send(None, [c_void_p, c_void_p, c_ulong])
        self._msg_send_1size_void = self._make_msg_send(None, [c_void_p, c_void_p, NSSize])

        self._status_item = None
        self._button = None
        self._target = None
        self._callback: Callable[[], None] | None = None
        self._imp = None

        self._setup()

    def set_click_callback(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def set_title(self, title: str) -> None:
        if self._button is None:
            return
        self._send(self._button, "setTitle:", self._nsstring(title))

    def set_tooltip(self, text: str) -> None:
        if self._button is None:
            return
        self._send(self._button, "setToolTip:", self._nsstring(text))

    def set_image(self, file_path: str, template: bool = True) -> None:
        if self._button is None:
            return
        image = self._nsimage_from_file(file_path)
        if image is None:
            return
        self._send_bool(image, "setTemplate:", bool(template))
        self._send_size(image, "setSize:", 16.0, 16.0)
        self._send(self._button, "setImage:", image)

    def set_image_png(self, png_bytes: bytes, template: bool = True) -> None:
        if self._button is None:
            return
        image = self._nsimage_from_png_bytes(png_bytes)
        if image is None:
            return
        self._send_bool(image, "setTemplate:", bool(template))
        self._send_size(image, "setSize:", 16.0, 16.0)
        self._send(self._button, "setImage:", image)

    def set_image_scaling_proportionally_down(self) -> None:
        if self._button is None:
            return
        self._send_uint(self._button, "setImageScaling:", 0)

    def remove(self) -> None:
        if self._status_item is None:
            return
        status_bar = self._send_class("NSStatusBar", "systemStatusBar")
        self._send(status_bar, "removeStatusItem:", self._status_item)
        self._status_item = None
        self._button = None
        self._target = None

    def _setup(self) -> None:
        status_bar = self._send_class("NSStatusBar", "systemStatusBar")
        status_item = self._send_double(status_bar, "statusItemWithLength:", -1.0)
        self._status_item = status_item
        self._button = self._send(self._status_item, "button")

        target = self._make_target()
        self._target = target
        self._send(self._button, "setTarget:", target)
        self._send(self._button, "setAction:", self._sel("trayClicked:"))

    def _make_target(self) -> c_void_p:
        nsobject = self._objc.objc_getClass(b"NSObject")
        self._objc.objc_allocateClassPair.restype = c_void_p
        self._objc.objc_allocateClassPair.argtypes = [c_void_p, c_char_p, ctypes.c_size_t]
        self._objc.objc_registerClassPair.restype = None
        self._objc.objc_registerClassPair.argtypes = [c_void_p]
        self._objc.class_addMethod.restype = c_bool
        self._objc.class_addMethod.argtypes = [c_void_p, c_void_p, c_void_p, c_char_p]

        cls_name = b"TraeTomatoTrayTarget"
        cls = self._objc.objc_allocateClassPair(nsobject, cls_name, 0)

        CALLBACK = ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_void_p)

        def _clicked(_self, _cmd, _sender):
            if self._callback is not None:
                self._callback()

        self._imp = CALLBACK(_clicked)
        ok = self._objc.class_addMethod(cls, self._sel("trayClicked:"), ctypes.cast(self._imp, c_void_p), b"v@:@")
        if not ok:
            cls = self._objc.objc_getClass(cls_name)
        else:
            self._objc.objc_registerClassPair(cls)

        obj = self._send(self._send(cls, "alloc"), "init")
        return obj

    def _send_class(self, class_name: str, selector: str, *args):
        cls = self._objc.objc_getClass(class_name.encode("utf-8"))
        return self._send(cls, selector, *args)

    def _sel(self, name: str) -> c_void_p:
        return self._objc.sel_registerName(name.encode("utf-8"))

    def _send(self, obj, selector: str, *args):
        sel = self._sel(selector)
        if not args:
            return self._msg_send_0(obj, sel)
        if len(args) != 1:
            raise ValueError("Unsupported objc_msgSend signature")
        return self._msg_send_1p(obj, sel, args[0])

    def _send_bool(self, obj, selector: str, value: bool) -> None:
        sel = self._sel(selector)
        self._msg_send_1b_void(obj, sel, c_bool(bool(value)))

    def _send_double(self, obj, selector: str, value: float) -> c_void_p:
        sel = self._sel(selector)
        return self._msg_send_1d(obj, sel, c_double(float(value)))

    def _send_uint(self, obj, selector: str, value: int) -> None:
        sel = self._sel(selector)
        self._msg_send_1u_void(obj, sel, c_ulong(int(value)))

    def _send_size(self, obj, selector: str, width: float, height: float) -> None:
        sel = self._sel(selector)
        self._msg_send_1size_void(obj, sel, NSSize(c_double(float(width)), c_double(float(height))))

    def _nsstring(self, value: str) -> c_void_p:
        nsstring = self._objc.objc_getClass(b"NSString")
        return self._send(nsstring, "stringWithUTF8String:", c_char_p(value.encode("utf-8")))

    def _nsimage_from_file(self, file_path: str) -> c_void_p | None:
        nsimage = self._objc.objc_getClass(b"NSImage")
        obj = self._send(nsimage, "alloc")
        img = self._send(obj, "initWithContentsOfFile:", self._nsstring(file_path))
        if img is None or img == 0:
            return None
        return img

    def _nsimage_from_png_bytes(self, png_bytes: bytes) -> c_void_p | None:
        buf_type = c_ubyte * len(png_bytes)
        buf = buf_type.from_buffer_copy(png_bytes)
        data = self._make_nsdata(buf, len(png_bytes))
        nsimage = self._objc.objc_getClass(b"NSImage")
        img = self._send(self._send(nsimage, "alloc"), "initWithData:", data)
        if img is None or img == 0:
            return None
        return img

    def _make_nsdata(self, buf, length: int) -> c_void_p:
        nsdata = self._objc.objc_getClass(b"NSData")
        sel = self._sel("dataWithBytes:length:")
        msg = self._make_msg_send(c_void_p, [c_void_p, c_void_p, c_void_p, c_size_t])
        return msg(nsdata, sel, ctypes.cast(buf, c_void_p), c_size_t(length))

    def _make_msg_send(self, restype, argtypes):
        return ctypes.CFUNCTYPE(restype, *argtypes)(("objc_msgSend", self._objc))
