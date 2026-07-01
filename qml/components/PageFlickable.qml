import QtQuick
import QtQuick.Controls

Flickable {
    id: root
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    contentWidth: width
    contentHeight: contentItem.childrenRect.height
    flickableDirection: Flickable.VerticalFlick
}
