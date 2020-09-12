
from PyQt5.QtWidgets import  QTabWidget, QTabBar, QWidget, QLabel, QVBoxLayout


class TabBar(QTabBar):
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)
        #self.tabSizeHint()


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        tab_bar = TabBar(self)
        self.setTabBar(tab_bar)
        self.setTabPosition(QTabWidget.West)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    w = TabWidget()
    for x in range(3):
        nw = QWidget()
        w.addTab(nw, "tab1")

    a = QWidget()
    l = QVBoxLayout(a)
    l.addWidget(w.tabBar())
    l.addWidget(QLabel('test'))
    l.addWidget(w)
    a.show()
    a.move(QCursor.pos())
    sys.exit(app.exec_())


# class TabBar: public QTabBar{
# public:
#     QSize tabSizeHint(int index) const{
#         QSize s = QTabBar::tabSizeHint(index);
#         s.transpose();
#         return s;
#     }
# protected:
#     void paintEvent(QPaintEvent * /*event*/){
#         QStylePainter painter(this);
#         QStyleOptionTab opt;
#
#         for(int i = 0;i < count();i++)
#         {
#             initStyleOption(&opt,i);
#             painter.drawControl(QStyle::CE_TabBarTabShape, opt);
#             painter.save();
#
#             QSize s = opt.rect.size();
#             s.transpose();
#             QRect r(QPoint(), s);
#             r.moveCenter(opt.rect.center());
#             opt.rect = r;
#
#             QPoint c = tabRect(i).center();
#             painter.translate(c);
#             painter.rotate(90);
#             painter.translate(-c);
#             painter.drawControl(QStyle::CE_TabBarTabLabel,opt);
#             painter.restore();
#         }
#     }
# };
#
# class TabWidget : public QTabWidget
# {
# public:
#     TabWidget(QWidget *parent=0):QTabWidget(parent){
#         setTabBar(new TabBar);
#         setTabPosition(QTabWidget::West);
#     }
# };
#
# int main(int argc, char *argv[])
# {
#     QApplication a(argc, argv);
#     TabWidget w;
#     w.addTab(new QWidget, "tab1");
#     w.addTab(new QWidget, "tab2");
#     w.addTab(new QWidget, "tab3");
#     w.show();
#
#     return a.exec();
# }