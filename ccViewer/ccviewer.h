#pragma once

// ##########################################################################
// #                                                                        #
// #                   CLOUDCOMPARE LIGHT VIEWER                            #
// #                                                                        #
// #  This program is free software; you can redistribute it and/or modify  #
// #  it under the terms of the GNU General Public License as published by  #
// #  the Free Software Foundation; version 2 or later of the License.      #
// #                                                                        #
// #      +++ COPYRIGHT: EDF R&D + TELECOM ParisTech (ENST-TSI) +++         #
// #                                                                        #
// ##########################################################################

// Qt
#include <QMainWindow>
#include <QStringList>
#include <QDockWidget>

// CCPluginAPI
#include <ccMainAppInterface.h>

// GUIs
#include <ui_ccviewer.h>

// System
#include <set>

class ccGLWindowInterface;
class ccHObject;
class Mouse3DInput;
class ccDBRoot;
class QTreeView;
class ccClipBox;
class ccPointCloud;
class ccBBox;

//! Application main window
class ccViewer : public QMainWindow
    , public ccMainAppInterface
{
	Q_OBJECT

  public:
	//! Default constructor
	ccViewer(QWidget* parent = nullptr, Qt::WindowFlags flags = QFlags<Qt::WindowType>());

	//! Default destructor
	~ccViewer() override;

	//! Adds entity to display db
	void addToDB(ccHObject* entity,
	             bool       updateZoom       = false,
	             bool       autoExpandDBTree = true,
	             bool       checkDimensions  = false,
	             bool       autoRedraw       = true) override;

	//! Removes an entity from display db
	void removeFromDB(ccHObject* obj, bool autoDelete = true) override;

	//! Checks for loaded entities
	/** If none, a message is displayed to invite the user
	    to drag & drop files.
	**/
	bool checkForLoadedEntities();

  public:
	//! Tries to load (and then adds to main db) a list of entity (files)
	/** \param filenames filenames to load
	    \return the first loaded entity/group
	**/
	ccHObject* addToDB(QStringList filenames);

  public: // ccMainInterface compliance
	QMainWindow* getMainWindow() override
	{
		return this;
	}
	ccGLWindowInterface* getActiveGLWindow() override
	{
		return m_glWindow;
	}
	ccHObject* loadFile(QString filename, bool silent) override
	{
		return addToDB(QStringList{filename});
	}
	void setSelectedInDB(ccHObject* obj, bool selected) override;
	[[nodiscard]] const ccHObject::Container& getSelectedEntities() const override;
	void                        dispToConsole(QString message, ConsoleMessageLevel level = STD_CONSOLE_MESSAGE) override;
	[[nodiscard]] ccHObject*    dbRootObject() override;
	void                        redrawAll(bool only2D = false) override;
	void                        refreshAll(bool only2D = false) override;
	void                        enableAll() override;
	void                        disableAll() override;
	void                        disableAllBut(ccGLWindowInterface* win) override;
	void                        updateUI() override;
	void freezeUI(bool state) override
	{
	}
	void setView(CC_VIEW_ORIENTATION view) override;
	void toggleActiveWindowCenteredPerspective() override;
	void toggleActiveWindowCustomLight() override;
	void toggleActiveWindowSunLight() override;
	void toggleActiveWindowViewerBasedPerspective() override;
	void zoomOnSelectedEntities() override
	{
		zoomOnSelectedEntity();
	}
	void                        increasePointSize() override;
	void                        decreasePointSize() override;
	[[nodiscard]] ccUniqueIDGenerator::Shared getUniqueIDGenerator() override;

  protected:
	//! Shows display parameters dialog
	void showDisplayParameters();

	//! Updates display to match display parameters
	void updateDisplay();

	//! Selects entity
	void selectEntity(ccHObject* entity);

	//! Delete selected entity
	void doActionDeleteSelectedEntity();

	//! Slot called when the exclusive full screen mode is called
	void onExclusiveFullScreenToggled(bool);

	void doActionEditCamera();
	void toggleSunLight(bool);
	void toggleCustomLight(bool);
	void toggleStereoMode(bool);
	void toggleFullScreen(bool);
	void toggleRotationAboutVertAxis();
	void doActionAbout();
	void doActionDisplayShortcuts();
	void setPivotAlwaysOn();
	void setPivotRotationOnly();
	void setPivotOff();
	void setOrthoView();
	void setCenteredPerspectiveView();
	void setViewerPerspectiveView();
	void setGlobalZoom() override;
	void zoomOnSelectedEntity();

	// default views
	void setFrontView();
	void setBottomView();
	void setTopView();
	void setBackView();
	void setLeftView();
	void setRightView();
	void setIsoView1();
	void setIsoView2();

	// selected entity properties
	void toggleColorsShown(bool);
	void toggleNormalsShown(bool);
	void toggleMaterialsShown(bool);
	void toggleScalarShown(bool);
	void toggleColorbarShown(bool);
	void changeCurrentScalarField(bool);

	// 3D mouse
	void on3DMouseMove(std::vector<float>&);
	void on3DMouseKeyUp(int);
	void on3DMouseKeyDown(int);
	void on3DMouseCMDKeyDown(int);
	void on3DMouseCMDKeyUp(int);
	void on3DMouseReleased();
	void enable3DMouse(bool state);

	// GL filters
	void doEnableGLFilter();
	void doDisableGLFilter();

	// Change the currently displayed SF
	void selectNextSF(int deltaPos);

	// === SLIM: Point cloud processing actions ===
	void doActionComputeNormals();
	void doActionSubsample();
	void doActionFilterByValue();
	void doActionSORFilter();

	// === SLIM: Tools menu actions ===
	void doActionClipBox();
	void doActionTLSPlane();
	void doActionPointProjection();
	void doActionKNNSearch();
	void doActionRotationMatrix();

	// === SLIM: New native C++ Tools menu actions ===
	void doActionBoundaryExtract();
	void doActionFoldExtract();
	void doActionSphereNeighborhood();
	void doActionSpherePCA();

	//! Slot called each time the clipping box is moved/resized
	void onClipBoxModified(const ccBBox* box);

  protected: // methods
	//! Loads plugins (from files)
	void loadPlugins();

	//! Loads Standard-type plugins (Python/MATLAB extension point)
	void loadStandardPlugins();


	//! Makes the GL frame background gradient match the OpenGL window one
	void updateGLFrameGradient();

	//! Updates perspective UI elements
	void reflectPerspectiveState();

	//! Updates pivot UI elements
	void reflectPivotVisibilityState();

	//! Updates lights UI elements
	void reflectLightsState();

	//! Checks whether stereo mode can be stopped (if necessary) or not
	bool checkStereoMode();

	// === SLIM: Clipping box helpers ===
	//! Removes the clipping box from the display and resets the tool state
	void closeClipBox();

  protected: // members
	//! Releases any connected 3D mouse (if any)
	void release3DMouse();

	//! Associated GL context
	ccGLWindowInterface* m_glWindow;

	//! Currently selected object
	ccHObject* m_selectedObject;

	//! 3D mouse handler
	Mouse3DInput* m_3dMouseInput;


	// === SLIM: Processing menu ===
	//! Processing menu
	QMenu* m_processingMenu;
	//! Processing actions
	QAction* m_actionNormals;
	QAction* m_actionSubsample;
	QAction* m_actionFilterByValue;
	QAction* m_actionSORFilter;

	// === SLIM: Tools menu ===
	//! Tools menu
	QMenu* m_toolsMenu;
	//! Tools actions
	QAction* m_actionClipBox;
	QAction* m_actionTLSPlane;
	QAction* m_actionPointProjection;
	QAction* m_actionKNN;
	QAction* m_actionRotationMatrix;

	// === SLIM: New native C++ Tools menu actions ===
	QAction* m_actionBoundaryExtract;
	QAction* m_actionFoldExtract;
	QAction* m_actionSphereNeighborhood;
	QAction* m_actionSpherePCA;

	// === SLIM: Clipping box ===
	//! Clipping box (owned by ccViewer, added to the GL window own DB while active)
	ccClipBox* m_clipBox;
	//! Whether the clipping box tool is currently active
	bool m_clipBoxActive;
	//! Cloud the clipping box was activated on (apply target)
	ccPointCloud* m_clipBoxCloud;

	// === SLIM: Selection tracking for plugins ===
	mutable ccHObject::Container m_selectedEntities;

  private:
	//! Associated GUI
	Ui::ccViewerClass ui;
};
