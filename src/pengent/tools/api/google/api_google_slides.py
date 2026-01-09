import os
import json
from typing import Optional, List, Union, Dict, Any
from enum import Enum
from dataclasses import dataclass
import uuid

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ....lib.custom_logger import get_logger

logger = get_logger()


@dataclass
class Color:
    """RGBカラーを表すクラス"""
    r: float
    g: float
    b: float

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            raise ValueError("Hex color must be 6 digits (e.g. #ff0000)")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return cls(r=r, g=g, b=b)

    @classmethod
    def from_dict(cls, data: dict) -> "Color":
        return cls(r=data.get("r", 0.0), g=data.get("g", 0.0), b=data.get("b", 0.0))

    @classmethod
    def from_value(cls, value) -> "Color":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_hex(value)
        if isinstance(value, dict):
            return cls.from_dict(value)
        raise TypeError(f"Unsupported color format: {value}")

    def to_rgb_color(self) -> dict:
        return {"rgbColor": {"red": self.r, "green": self.g, "blue": self.b}}


@dataclass
class TextBoxComponent:
    """テキストボックスコンポーネント"""
    text: str
    position: Optional[dict] = None
    size: Optional[dict] = None
    object_id: Optional[str] = None
    text_color: Optional[Color] = None
    background_color: Optional[Color] = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            text=data.get("text", ""),
            position=data.get("position"),
            size=data.get("size"),
            object_id=data.get("object_id"),
            text_color=Color.from_value(data.get("text_color"))
            if data.get("text_color")
            else None,
            background_color=Color.from_value(data.get("background_color"))
            if data.get("background_color")
            else None,
        )

    def with_defaults(
        self, default_position: dict, default_size: dict
    ) -> "TextBoxComponent":
        return TextBoxComponent(
            text=self.text,
            position=self.position or default_position,
            size=self.size or default_size,
            object_id=self.object_id,
            text_color=self.text_color,
            background_color=self.background_color,
        )

    def to_create_requests(self, slide_id: str) -> List[dict]:
        transform = {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": self.position["x"],
            "translateY": self.position["y"],
            "unit": "PT",
        }

        base_props = {
            "pageObjectId": slide_id,
            "size": {
                "height": {"magnitude": self.size["height"], "unit": "PT"},
                "width": {"magnitude": self.size["width"], "unit": "PT"},
            },
            "transform": transform,
        }

        requests = [
            {
                "createShape": {
                    "objectId": self.object_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": base_props,
                }
            },
            {
                "insertText": {
                    "objectId": self.object_id,
                    "insertionIndex": 0,
                    "text": self.text,
                }
            },
        ]
        return requests

    def to_update_requests(self, default_size: dict) -> List[dict]:
        requests = [
            {"deleteText": {"objectId": self.object_id, "textRange": {"type": "ALL"}}},
            {
                "insertText": {
                    "objectId": self.object_id,
                    "insertionIndex": 0,
                    "text": self.text,
                }
            },
        ]
        # transform
        position = self.position or {"x": 100, "y": 100}
        size = self.size or default_size
        transform = {
            "scaleX": size["width"] / 100,
            "scaleY": size["height"] / 100,
            "translateX": position["x"],
            "translateY": position["y"],
            "unit": "PT",
        }

        requests.append(
            {
                "updatePageElementTransform": {
                    "objectId": self.object_id,
                    "applyMode": "ABSOLUTE",
                    "transform": transform,
                }
            }
        )
        return requests


@dataclass
class ImageComponent:
    """画像コンポーネント"""
    image_url: str
    position: Optional[dict] = None
    size: Optional[dict] = None
    object_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            image_url=data["image_url"],
            position=data.get("position"),
            size=data.get("size"),
            object_id=data.get("object_id"),
        )

    def with_defaults(
        self, default_position: dict, default_size: dict
    ) -> "ImageComponent":
        return ImageComponent(
            image_url=self.image_url,
            position=self.position or default_position,
            size=self.size or default_size,
            object_id=self.object_id,
        )

    def to_create_requests(self, slide_id: str) -> list[dict]:
        transform = {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": self.position["x"],
            "translateY": self.position["y"],
            "unit": "PT",
        }

        props = {
            "pageObjectId": slide_id,
            "size": {
                "height": {"magnitude": self.size["height"], "unit": "PT"},
                "width": {"magnitude": self.size["width"], "unit": "PT"},
            },
            "transform": transform,
        }

        return [
            {
                "createImage": {
                    "objectId": self.object_id,
                    "url": self.image_url,
                    "elementProperties": props,
                }
            }
        ]


@dataclass
class TableStyle:
    """テーブルスタイル設定"""
    header_bold: bool = True
    header_background_color: Optional[Union[Color, str, dict]] = Color.from_hex(
        "#eeeeee"
    )

    def to_requests(
        self, object_id: str, column_count: int, row_index: int = 0
    ) -> List[dict]:
        color = Color.from_value(self.header_background_color)
        requests = []

        for col in range(column_count):
            cell_location = {"rowIndex": row_index, "columnIndex": col}

            if self.header_bold:
                requests.append(
                    {
                        "updateTextStyle": {
                            "objectId": object_id,
                            "cellLocation": cell_location,
                            "style": {"bold": True},
                            "textRange": {"type": "ALL"},
                            "fields": "bold",
                        }
                    }
                )

            requests.append(
                {
                    "updateTableCellProperties": {
                        "objectId": object_id,
                        "tableRange": {
                            "location": cell_location,
                            "rowSpan": 1,
                            "columnSpan": 1,
                        },
                        "tableCellProperties": {
                            "tableCellBackgroundFill": {
                                "solidFill": {"color": color.to_rgb_color()}
                            }
                        },
                        "fields": "tableCellBackgroundFill.solidFill.color",
                    }
                }
            )

        return requests


@dataclass
class TableComponent:
    """テーブルコンポーネント"""
    data: List[List[str]]
    position: Optional[dict] = None
    size: Optional[dict] = None
    object_id: Optional[str] = None
    style: Optional[TableStyle] = None
    row_height: Optional[float] = 20.0

    @classmethod
    def from_dict(cls, d: dict) -> "TableComponent":
        return cls(
            data=d.get("data", []),
            position=d.get("position"),
            size=d.get("size"),
            object_id=d.get("object_id"),
            style=TableStyle(
                header_bold=d.get("header_bold", True),
                header_background_color=d.get("header_background_color", "#eeeeee"),
            )
            if "header_background_color" in d or "header_bold" in d
            else None,
        )

    def to_row_height_requests(self) -> List[dict]:
        if not self.object_id or self.row_height is None:
            return []
        return [
            {
                "updateTableRowProperties": {
                    "objectId": self.object_id,
                    "rowIndices": list(range(self.row_count())),
                    "tableRowProperties": {
                        "minRowHeight": {"magnitude": self.row_height, "unit": "PT"}
                    },
                    "fields": "minRowHeight",
                }
            }
        ]

    def row_count(self) -> int:
        return len(self.data)

    def col_count(self) -> int:
        return max(len(row) for row in self.data) if self.data else 0

    def to_style_requests(self) -> List[dict]:
        if not self.style or not self.object_id:
            return []
        return self.style.to_requests(self.object_id, self.col_count(), row_index=0)


class ShapeType(str, Enum):
    """図形の種類"""
    RIGHT_ARROW = "RIGHT_ARROW"
    LEFT_ARROW = "LEFT_ARROW"
    CHECKMARK = "CHECKMARK"
    STAR_5 = "STAR_5"
    ELLIPSE = "ELLIPSE"
    RECTANGLE = "RECTANGLE"
    CALLOUT_WEDGE_RECTANGLE = "CALLOUT_WEDGE_RECTANGLE"


@dataclass
class ShapeStyle:
    """図形スタイル設定"""
    fill_color: Optional[Union[str, dict, Color]] = None
    border_color: Optional[Union[str, dict, Color]] = None
    border_weight: Optional[float] = None  # pt

    def to_requests(self, object_id: str) -> List[dict]:
        requests = []

        props: Dict[str, Any] = {}
        fields = []

        if self.fill_color:
            fill = Color.from_value(self.fill_color).to_rgb_color()
            props["shapeBackgroundFill"] = {"solidFill": {"color": fill}}
            fields.append("shapeBackgroundFill.solidFill.color")

        if self.border_color:
            border = Color.from_value(self.border_color).to_rgb_color()
            props.setdefault("outline", {})["outlineFill"] = {
                "solidFill": {"color": border}
            }
            fields.append("outline.outlineFill.solidFill.color")

        if self.border_weight is not None:
            props.setdefault("outline", {})["weight"] = {
                "magnitude": self.border_weight,
                "unit": "PT",
            }
            fields.append("outline.weight")

        if props and fields:
            requests.append(
                {
                    "updateShapeProperties": {
                        "objectId": object_id,
                        "shapeProperties": props,
                        "fields": ",".join(fields),
                    }
                }
            )

        return requests


@dataclass
class ShapeComponent:
    """図形コンポーネント"""
    shape_type: str  # 例: "RIGHT_ARROW", "CHECKMARK"
    text: Optional[str] = ""
    position: Optional[dict] = None
    size: Optional[dict] = None
    object_id: Optional[str] = None
    style: Optional[ShapeStyle] = None

    @classmethod
    def from_dict(cls, d: dict) -> "ShapeComponent":
        return cls(
            shape_type=d["shape_type"],
            text=d.get("text", ""),
            position=d.get("position"),
            size=d.get("size"),
            object_id=d.get("object_id"),
            style=ShapeStyle(
                fill_color=d.get("fill_color"),
                border_color=d.get("border_color"),
                border_weight=d.get("border_weight"),
            )
            if "fill_color" in d or "border_color" in d
            else None,
        )

    def with_defaults(
        self, default_position: dict, default_size: dict
    ) -> "ShapeComponent":
        return ShapeComponent(
            shape_type=self.shape_type,
            text=self.text,
            position=self.position or default_position,
            size=self.size or default_size,
            object_id=self.object_id,
            style=self.style,
        )


class ApiGoogleSlides:
    """Google Slides APIクライアント"""
    def __init__(self, token_file: str = "token.json"):
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file not found: {token_file}")
        with open(token_file, "r") as f:
            creds_data = json.load(f)
        self.creds = Credentials.from_authorized_user_info(creds_data)
        self.service = build("slides", "v1", credentials=self.creds)

    def create_presentation(self, title: str) -> str:
        body = {"title": title}
        presentation = self.service.presentations().create(body=body).execute()
        return presentation["presentationId"]

    def get_slides(self, presentation_id: str) -> list[str]:
        """
        指定されたプレゼンテーションの全スライドのID一覧を返す
        """
        presentation = (
            self.service.presentations().get(presentationId=presentation_id).execute()
        )
        slides = presentation.get("slides", [])
        return [slide["objectId"] for slide in slides]

    def show_slide(self, presentation_id: str, slide_object_id: str) -> dict:
        """
        指定されたスライドの詳細情報を取得
        """
        presentation = (
            self.service.presentations().get(presentationId=presentation_id).execute()
        )
        for slide in presentation.get("slides", []):
            if slide["objectId"] == slide_object_id:
                return slide
        raise ValueError(f"Slide ID {slide_object_id} not found")

    def add_slide(
        self,
        presentation_id: str,
        layout: str = "TITLE_AND_BODY",
        title: str = "",
        body: str = "",
    ) -> str:
        # 1. スライドを追加
        (
            self.service.presentations()
            .batchUpdate(
                presentationId=presentation_id,
                body={
                    "requests": [
                        {
                            "createSlide": {
                                "slideLayoutReference": {"predefinedLayout": layout}
                            }
                        }
                    ]
                },
            )
            .execute()
        )

        # 2. 最新のスライドを取得
        presentation = (
            self.service.presentations().get(presentationId=presentation_id).execute()
        )
        slide = presentation["slides"][-1]  # 最後のスライド
        title_id = None
        body_id = None

        # 3. テキストボックスの objectId を取得
        for element in slide.get("pageElements", []):
            logger.debug(element)
            shape = element.get("shape")
            if not shape:
                continue
            logger.debug(f"shape:{shape}")
            logger.debug(f"placeholder:{shape['placeholder']}")

            shape_type = shape.get("shapeType")
            placeholder_type = shape.get("placeholder", {}).get("type")
            if (
                shape_type == "TEXT_BOX"
                and placeholder_type == "TITLE"
                and not title_id
            ):
                logger.debug("TEXT_BOX")
                title_id = element["objectId"]
            elif (
                shape_type == "TEXT_BOX" and placeholder_type == "BODY" and not body_id
            ):
                logger.debug("BODY")
                body_id = element["objectId"]

        def has_text(presentation, object_id):
            for slide in presentation.get("slides", []):
                for element in slide.get("pageElements", []):
                    if element.get("objectId") == object_id:
                        text_elements = (
                            element.get("shape", {})
                            .get("text", {})
                            .get("textElements", [])
                        )
                        return any("textRun" in te for te in text_elements)
            return False

        # 4. リクエストを構築
        requests = []
        if title_id and title:
            if has_text(presentation, title_id):
                requests.append(
                    {"deleteText": {"objectId": title_id, "textRange": {"type": "ALL"}}}
                )
            requests.append(
                {
                    "insertText": {
                        "objectId": title_id,
                        "text": title,
                        "insertionIndex": 0,
                    }
                }
            )

        if body_id and body:
            if has_text(presentation, body_id):
                requests.append(
                    {"deleteText": {"objectId": body_id, "textRange": {"type": "ALL"}}}
                )
            requests.append(
                {"insertText": {"objectId": body_id, "text": body, "insertionIndex": 0}}
            )

        # 5. リクエストを実行
        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": requests}
            ).execute()

        return slide["objectId"]

    def delete_slide(self, presentation_id: str, slide_object_id: str):
        """
        指定されたスライドを削除
        """
        self.service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": [{"deleteObject": {"objectId": slide_object_id}}]},
        ).execute()
        logger.debug(
            f"Slide {slide_object_id} deleted from presentation {presentation_id}"
        )
        return True

    def clear_slide(self, presentation_id: str, slide_object_id: str):
        """
        指定スライド内の全コンポーネント(図形・画像・テキストなど)を削除する
        """
        slide = self.show_slide(presentation_id, slide_object_id)
        requests = []
        for element in slide.get("pageElements", []):
            requests.append({"deleteObject": {"objectId": element["objectId"]}})
        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": requests}
            ).execute()

    def _default_position(self, slide_elements: list, index: int = None):
        """
        スライド内の要素に応じて位置をずらす。index があればその順に配置。
        """
        base_y = 50
        offset_y = 50
        i = index if index is not None else len(slide_elements)
        return {"x": 100, "y": base_y + offset_y * i}

    def _default_size(self, type_: str):
        if type_ == "text_box":
            return {"width": 400, "height": 50}
        elif type_ == "image":
            return {"width": 300, "height": 200}
        return {"width": 200, "height": 100}

    def _to_rgb_color(color_dict):
        return {
            "rgbColor": {
                "red": color_dict.get("r", 0),
                "green": color_dict.get("g", 0),
                "blue": color_dict.get("b", 0),
            }
        }

    def _create_style_requests(
        self,
        object_id: str,
        *,
        text_color: Color = None,
        background_color: Color = None,
    ):
        requests = []

        if text_color:
            requests.append(
                {
                    "updateTextStyle": {
                        "objectId": object_id,
                        "textRange": {"type": "ALL"},
                        "style": {
                            "foregroundColor": {
                                "opaqueColor": text_color.to_rgb_color()
                            }
                        },
                        "fields": "foregroundColor",
                    }
                }
            )

        if background_color:
            requests.append(
                {
                    "updateShapeProperties": {
                        "objectId": object_id,
                        "shapeProperties": {
                            "shapeBackgroundFill": {
                                "solidFill": {"color": background_color.to_rgb_color()}
                            }
                        },
                        "fields": "shapeBackgroundFill.solidFill.color",
                    }
                }
            )

        return requests

    def add_text_box(
        self,
        presentation_id: str,
        slide_object_id: str,
        component: Union[TextBoxComponent, dict],
    ):
        if isinstance(component, dict):
            component = TextBoxComponent.from_dict(component)

        slide = self.show_slide(presentation_id, slide_object_id)
        elements = slide.get("pageElements", [])

        object_id = component.object_id or f"obj_{uuid.uuid4().hex[:8]}"
        if component.object_id and any(
            el.get("objectId") == component.object_id for el in elements
        ):
            return self.update_text_box(presentation_id, component)

        component = component.with_defaults(
            default_position=self._default_position(elements),
            default_size=self._default_size("text_box"),
        )
        component.object_id = object_id

        requests = component.to_create_requests(slide_object_id)
        requests += self._create_style_requests(
            object_id,
            text_color=component.text_color,
            background_color=component.background_color,
        )

        self.service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()
        return object_id

    def update_text_box(
        self, presentation_id: str, component: Union[TextBoxComponent, dict]
    ):
        if isinstance(component, dict):
            component = TextBoxComponent.from_dict(component)

        if not component.object_id:
            raise ValueError("object_id is required for update_text_box")

        requests = component.to_update_requests(self._default_size("text_box"))
        requests += self._create_style_requests(
            component.object_id,
            text_color=component.text_color,
            background_color=component.background_color,
        )

        self.service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()
        return component.object_id

    def add_image(
        self,
        presentation_id: str,
        slide_object_id: str,
        component: Union[ImageComponent, dict],
    ) -> str:
        if isinstance(component, dict):
            component = ImageComponent.from_dict(component)

        slide = self.show_slide(presentation_id, slide_object_id)
        elements = slide.get("pageElements", [])

        object_id = component.object_id or f"obj_{uuid.uuid4().hex[:8]}"
        if component.object_id and any(
            el.get("objectId") == component.object_id for el in elements
        ):
            logger.warning(
                "Image already exists. Currently no update_image method implemented."
            )
            return component.object_id

        component = component.with_defaults(
            default_position=self._default_position(elements),
            default_size=self._default_size("image"),
        )
        component.object_id = object_id

        requests = component.to_create_requests(slide_object_id)
        self.service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()
        return object_id

    def update_image(
        self, presentation_id: str, component: Union[ImageComponent, dict]
    ) -> str:
        if isinstance(component, dict):
            component = ImageComponent.from_dict(component)

        if not component.object_id:
            raise ValueError("object_id is required for update_image")

        requests = []

        # 画像差し替え
        requests.append(
            {
                "replaceImage": {
                    "imageObjectId": component.object_id,
                    "url": component.image_url,
                }
            }
        )

        # transform(位置＋サイズ)の更新
        position = component.position or {"x": 100, "y": 100}
        size = component.size or self._default_size("image")
        transform = {
            "scaleX": size["width"] / 100,
            "scaleY": size["height"] / 100,
            "translateX": position["x"],
            "translateY": position["y"],
            "unit": "PT",
        }

        requests.append(
            {
                "updatePageElementTransform": {
                    "objectId": component.object_id,
                    "applyMode": "ABSOLUTE",
                    "transform": transform,
                }
            }
        )

        self.service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()

        return component.object_id

    def add_table(
        self,
        presentation_id: str,
        slide_object_id: str,
        component: Union[TableComponent, dict],
    ) -> str:
        if isinstance(component, dict):
            component = TableComponent.from_dict(component)

        slide = self.show_slide(presentation_id, slide_object_id)
        elements = slide.get("pageElements", [])

        object_id = component.object_id or f"tbl_{uuid.uuid4().hex[:8]}"
        component.object_id = object_id
        position = component.position or self._default_position(elements)
        size = component.size or {"width": 400, "height": 100}

        transform = {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": position["x"],
            "translateY": position["y"],
            "unit": "PT",
        }

        create_table_request = {
            "createTable": {
                "objectId": object_id,
                "elementProperties": {
                    "pageObjectId": slide_object_id,
                    "size": {
                        "width": {"magnitude": size["width"], "unit": "PT"},
                        "height": {"magnitude": size["height"], "unit": "PT"},
                    },
                    "transform": transform,
                },
                "rows": component.row_count(),
                "columns": component.col_count(),
            }
        }

        # insertText リクエスト作成
        insert_requests = []
        for r, row in enumerate(component.data):
            for c, cell_text in enumerate(row):
                insert_requests.append(
                    {
                        "insertText": {
                            "objectId": object_id,
                            "cellLocation": {"rowIndex": r, "columnIndex": c},
                            "text": cell_text,
                            "insertionIndex": 0,
                        }
                    }
                )

        self.service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": [create_table_request] + insert_requests},
        ).execute()

        # 2回目: スタイル適用(createTable 完了後)
        style_requests = component.to_style_requests()
        row_height_requests = component.to_row_height_requests()
        print(style_requests)

        if style_requests or row_height_requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": style_requests + row_height_requests},
            ).execute()

        return object_id

    def update_table(
        self, presentation_id: str, component: Union[TableComponent, dict]
    ) -> str:
        if isinstance(component, dict):
            component = TableComponent.from_dict(component)

        if not component.object_id:
            raise ValueError("object_id is required to update the table")

        requests = []

        for r, row in enumerate(component.data):
            for c, cell_text in enumerate(row):
                requests.append(
                    {
                        "deleteText": {
                            "objectId": component.object_id,
                            "cellLocation": {"rowIndex": r, "columnIndex": c},
                            "textRange": {"type": "ALL"},
                        }
                    }
                )
                requests.append(
                    {
                        "insertText": {
                            "objectId": component.object_id,
                            "cellLocation": {"rowIndex": r, "columnIndex": c},
                            "insertionIndex": 0,
                            "text": cell_text,
                        }
                    }
                )

        # スタイルと行高さを適用(オプション)
        requests += component.to_style_requests()
        requests += component.to_row_height_requests()

        # 実行
        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": requests}
            ).execute()

        return component.object_id

    def add_shape(
        self,
        presentation_id: str,
        slide_object_id: str,
        component: Union[ShapeComponent, dict],
    ) -> str:
        if isinstance(component, dict):
            component = ShapeComponent.from_dict(component)

        slide = self.show_slide(presentation_id, slide_object_id)
        elements = slide.get("pageElements", [])

        object_id = component.object_id or f"shape_{uuid.uuid4().hex[:8]}"
        component.object_id = object_id
        component = component.with_defaults(
            default_position=self._default_position(elements),
            default_size={"width": 100, "height": 100},
        )

        transform = {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": component.position["x"],
            "translateY": component.position["y"],
            "unit": "PT",
        }

        props = {
            "pageObjectId": slide_object_id,
            "size": {
                "height": {"magnitude": component.size["height"], "unit": "PT"},
                "width": {"magnitude": component.size["width"], "unit": "PT"},
            },
            "transform": transform,
        }

        shape_type = component.shape_type

        requests = [
            {
                "createShape": {
                    "objectId": object_id,
                    "shapeType": shape_type,
                    "elementProperties": props,
                }
            }
        ]

        if component.text:
            requests.append(
                {
                    "insertText": {
                        "objectId": object_id,
                        "insertionIndex": 0,
                        "text": component.text,
                    }
                }
            )

        # スタイルも反映
        if component.style:
            requests += component.style.to_requests(object_id)

        self.service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()

        return object_id

    def update_shape(
        self, presentation_id: str, component: Union[ShapeComponent, dict]
    ) -> str:
        if isinstance(component, dict):
            component = ShapeComponent.from_dict(component)

        if not component.object_id:
            raise ValueError("object_id is required for update_shape")

        requests = []

        # 1. テキスト更新
        if component.text is not None:
            requests.append(
                {
                    "deleteText": {
                        "objectId": component.object_id,
                        "textRange": {"type": "ALL"},
                    }
                }
            )
            requests.append(
                {
                    "insertText": {
                        "objectId": component.object_id,
                        "insertionIndex": 0,
                        "text": component.text,
                    }
                }
            )

        # 2. 位置・サイズ(transform)更新
        if component.position or component.size:
            position = component.position or {"x": 100, "y": 100}
            size = component.size or {"width": 100, "height": 100}
            transform = {
                "scaleX": size["width"] / 100,
                "scaleY": size["height"] / 100,
                "translateX": position["x"],
                "translateY": position["y"],
                "unit": "PT",
            }
            requests.append(
                {
                    "updatePageElementTransform": {
                        "objectId": component.object_id,
                        "applyMode": "ABSOLUTE",
                        "transform": transform,
                    }
                }
            )

        # 3. スタイル(色・枠線など)
        if component.style:
            requests += component.style.to_requests(component.object_id)

        # 実行
        if requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": requests}
            ).execute()

        return component.object_id

    def add_components(
        self, presentation_id: str, slide_object_id: str, components: List[dict]
    ) -> List[str]:
        object_ids = []

        for comp in components:
            comp_type = comp.get("type")
            if not comp_type:
                raise ValueError("Each component must have a 'type' field")

            if comp_type == "text_box":
                object_id = self.add_text_box(presentation_id, slide_object_id, comp)
            elif comp_type == "image":
                object_id = self.add_image(presentation_id, slide_object_id, comp)
            elif comp_type == "shape":
                object_id = self.add_shape(presentation_id, slide_object_id, comp)
            elif comp_type == "table":
                object_id = self.add_table(presentation_id, slide_object_id, comp)
            else:
                raise ValueError(f"Unsupported component type: {comp_type}")

            object_ids.append(object_id)

        return object_ids
