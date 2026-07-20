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

#include "ccviewer.h"

#include "ccViewerApplication.h"
#include "ccviewerlog.h"

// Qt
#include <QMessageBox>
#include <QShortcut>
#include <QDockWidget>
#include <QTreeView>
#include <QVBoxLayout>
#include <QFileDialog>

// qCC_glWindow
#include <ccGLWindowInterface.h>

// common dialogs
#include <ccCameraParamEditDlg.h>
#include <ccDisplaySettingsDlg.h>
#include <ccStereoModeDlg.h>

// qCC_db
#include <ccGenericMesh.h>
#include <ccHObjectCaster.h>
#include <ccPointCloud.h>
#include <ccHObject.h>

// plugins
#include "ccGLPluginInterface.h"
#include "ccIOPluginInterface.h"
#include "ccStdPluginInterface.h"
#include "ccPluginManager.h"

// 3D mouse handler
#ifdef CC_3DXWARE_SUPPORT
#include "Mouse3DInput.h"
#endif

// === SLIM: DB Tree & processing dialogs ===
#include "ccNormalComputationDlg.h"
#include "ccSubsamplingDlg.h"
#include "ccFilterByValueDlg.h"
#include "ccSORFilterDlg.h"

// CCCoreLib (for SOR filter and scalar field access)
#include <CloudSamplingTools.h>
#include <ScalarField.h>

// Progress dialog
#include <ccProgressDialog.h>

// === SLIM: Clipping box & Python tools ===
#include <ccClipBox.h>

// === SLIM: Native C++ algorithm tools ===
#include "ccViewerAlgorithms.h"

#include <QCheckBox>
#include <QCoreApplication>
#include <QDialogButtonBox>
#include <QDir>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QInputDialog>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QProcess>
#include <QPushButton>
#include <QStandardPaths>
#include <QTemporaryFile>

// Camera parameters dialog
static ccCameraParamEditDlg* s_cpeDlg = nullptr;

ccViewer::ccViewer(QWidget* parent, Qt::WindowFlags flags)
    : QMainWindow(parent, flags)
    , m_glWindow(nullptr)
    , m_selectedObject(nullptr)
    , m_3dMouseInput(nullptr)
    , m_processingMenu(nullptr)
    , m_actionNormals(nullptr)
    , m_actionSubsample(nullptr)
    , m_actionFilterByValue(nullptr)
    , m_actionSORFilter(nullptr)
    , m_toolsMenu(nullptr)
    , m_actionClipBox(nullptr)
    , m_actionTLSPlane(nullptr)
    , m_actionPointProjection(nullptr)
    , m_actionKNN(nullptr)
    , m_actionRotationMatrix(nullptr)
    , m_actionBoundaryExtract(nullptr)
    , m_actionFoldExtract(nullptr)
    , m_actionSphereNeighborhood(nullptr)
    , m_actionSpherePCA(nullptr)
    , m_clipBox(nullptr)
    , m_clipBoxActive(false)
    , m_clipBoxCloud(nullptr)
{
	ui.setupUi(this);

#ifdef Q_OS_LINUX
	setStyleSheet("QStatusBar{background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,stop:0 rgb(200,200,200), stop:1 rgb(255,255,255));}");
#endif

	setWindowTitle(QString("ccViewer v%1").arg(ccApp->versionLongStr(false)));

	// insert GL window in a vertical layout
	{
		QVBoxLayout* verticalLayout = new QVBoxLayout(ui.GLframe);
		verticalLayout->setSpacing(0);
		const int margin = 10;
		verticalLayout->setContentsMargins(margin, margin, margin, margin);

		bool stereoMode = ccGLWindowInterface::TestStereoSupport();

		QWidget* glWidget = nullptr;
		ccGLWindowInterface::Create(m_glWindow, glWidget, stereoMode);
		assert(m_glWindow && glWidget);

		verticalLayout->addWidget(glWidget);
	}

	updateGLFrameGradient();

	m_glWindow->setRectangularPickingAllowed(false);

	// === SLIM: Create File menu (Open / Save) ===
	{
		QMenu* fileMenu = ui.menuBar->addMenu(tr("File"));

		QAction* actionOpen = fileMenu->addAction(tr("Open..."));
		actionOpen->setShortcut(QKeySequence::Open);
		connect(actionOpen, &QAction::triggered, this, [this]() {
			QStringList filenames = QFileDialog::getOpenFileNames(this,
				tr("Open File(s)"),
				QString(),
				tr("All supported (*.bin *.las *.laz *.txt *.asc *.neu *.xyz *.pts *.csv *.ply *.obj *.stl *.vtk *.off *.ptx *.sbf *.png *.jpg *.bmp);;All files (*.*)"));
			if (filenames.isEmpty())
				return;

			// Expand directories: if a path is actually a directory
			// (e.g. a folder named ".las" from archive extraction),
			// scan inside for supported files
			QStringList expandedFiles;
			QStringList supportedExts = {
				"*.bin","*.las","*.laz","*.txt","*.asc","*.neu","*.xyz",
				"*.pts","*.csv","*.ply","*.obj","*.stl","*.vtk","*.off",
				"*.ptx","*.sbf","*.png","*.jpg","*.bmp"
			};
			for (const QString& path : filenames)
			{
				QFileInfo fi(path);
				if (fi.isDir())
				{
					QDir dir(path);
					QList<QFileInfo> inner = dir.entryInfoList(supportedExts, QDir::Files | QDir::Readable, QDir::Name);
					for (const QFileInfo& f : inner)
						expandedFiles.append(f.absoluteFilePath());
				}
				else
				{
					expandedFiles.append(path);
				}
			}

			if (!expandedFiles.isEmpty())
				addToDB(expandedFiles);
		});

		QAction* actionSave = fileMenu->addAction(tr("Save As..."));
		actionSave->setShortcut(QKeySequence::SaveAs);
		actionSave->setEnabled(false);
		connect(actionSave, &QAction::triggered, this, [this]() {
			if (!m_selectedObject) return;
			QString filename = QFileDialog::getSaveFileName(this,
				tr("Save File"),
				QString(),
				tr("Supported (*.bin *.las *.laz *.txt *.ply *.obj *.stl *.vtk *.off *.ptx *.sbf *.png *.jpg *.bmp);;All files (*.*)"));
			if (filename.isEmpty()) return;
			FileIOFilter::SaveParameters saveParams;
			saveParams.parentWidget = this;
			saveParams.alwaysDisplaySaveDialog = false;
			CC_FILE_ERROR err = FileIOFilter::SaveToFile(m_selectedObject, filename, saveParams, QString());
			if (err != CC_FERR_NO_ERROR)
				ccLog::Error(QString("Failed to save: %1").arg(filename));
			else
				ccLog::Print(QString("Saved: %1").arg(filename));
		});

		// Enable save when entity selected
		connect(fileMenu, &QMenu::aboutToShow, this, [actionSave, this]() {
			actionSave->setEnabled(m_selectedObject != nullptr);
		});
	}



	// === SLIM: Create Processing menu ===
	{
		m_processingMenu = ui.menuBar->addMenu(tr("Processing"));

		m_actionNormals = m_processingMenu->addAction(tr("Compute Normals"));
		m_actionNormals->setEnabled(false);
		connect(m_actionNormals, &QAction::triggered, this, &ccViewer::doActionComputeNormals);

		m_actionSubsample = m_processingMenu->addAction(tr("Subsample"));
		m_actionSubsample->setEnabled(false);
		connect(m_actionSubsample, &QAction::triggered, this, &ccViewer::doActionSubsample);

		m_actionFilterByValue = m_processingMenu->addAction(tr("Filter by Value"));
		m_actionFilterByValue->setEnabled(false);
		connect(m_actionFilterByValue, &QAction::triggered, this, &ccViewer::doActionFilterByValue);

		

		m_actionSORFilter = m_processingMenu->addAction(tr("SOR Filter (Outlier Removal)"));
		m_actionSORFilter->setEnabled(false);
		connect(m_actionSORFilter, &QAction::triggered, this, &ccViewer::doActionSORFilter);


		



		m_processingMenu->addSeparator();

	}

	// === SLIM: Create Tools menu ===
	{
		m_toolsMenu = ui.menuBar->addMenu(tr("Tools"));

		// --- Clipping Box ---
		m_actionClipBox = m_toolsMenu->addAction(tr("Clip by Box"));
		m_actionClipBox->setCheckable(true);
		m_actionClipBox->setEnabled(false);
		connect(m_actionClipBox, &QAction::toggled, this, &ccViewer::doActionClipBox);

		m_toolsMenu->addSeparator();

		// --- TLS Plane Fitting ---
		m_actionTLSPlane = m_toolsMenu->addAction(tr("Plane Fitting (TLS)"));
		m_actionTLSPlane->setEnabled(false);
		connect(m_actionTLSPlane, &QAction::triggered, this, &ccViewer::doActionTLSPlane);

		// --- Point-to-Plane Projection ---
		m_actionPointProjection = m_toolsMenu->addAction(tr("Point to Plane Projection"));
		m_actionPointProjection->setEnabled(false);
		connect(m_actionPointProjection, &QAction::triggered, this, &ccViewer::doActionPointProjection);

		// --- KNN Search ---
		m_actionKNN = m_toolsMenu->addAction(tr("KNN Search"));
		m_actionKNN->setEnabled(false);
		connect(m_actionKNN, &QAction::triggered, this, &ccViewer::doActionKNNSearch);

		// --- Rotation Matrix ---
		m_actionRotationMatrix = m_toolsMenu->addAction(tr("Rotation Matrix"));
		m_actionRotationMatrix->setEnabled(true); // doesn't need cloud selection
		connect(m_actionRotationMatrix, &QAction::triggered, this, &ccViewer::doActionRotationMatrix);

		m_toolsMenu->addSeparator();

		// --- Boundary Point Extract (Native C++) ---
		m_actionBoundaryExtract = m_toolsMenu->addAction(tr("Boundary Point Extract"));
		m_actionBoundaryExtract->setEnabled(false);
		connect(m_actionBoundaryExtract, &QAction::triggered, this, &ccViewer::doActionBoundaryExtract);

		// --- Fold Point Extract (Native C++) ---
		m_actionFoldExtract = m_toolsMenu->addAction(tr("Fold Point Extract"));
		m_actionFoldExtract->setEnabled(false);
		connect(m_actionFoldExtract, &QAction::triggered, this, &ccViewer::doActionFoldExtract);

		// --- Sphere Neighborhood (Native C++) ---
		m_actionSphereNeighborhood = m_toolsMenu->addAction(tr("Sphere Neighborhood"));
		m_actionSphereNeighborhood->setEnabled(false);
		connect(m_actionSphereNeighborhood, &QAction::triggered, this, &ccViewer::doActionSphereNeighborhood);

		// --- Sphere PCA (Native C++) ---
		m_actionSpherePCA = m_toolsMenu->addAction(tr("Sphere PCA"));
		m_actionSpherePCA->setEnabled(false);
		connect(m_actionSpherePCA, &QAction::triggered, this, &ccViewer::doActionSpherePCA);
	}

	// UI/display synchronization
	ui.actionFullScreen->setChecked(false);
	ui.menuSelected->setEnabled(false);
	reflectLightsState();
	reflectPerspectiveState();
	reflectPivotVisibilityState();

#ifdef CC_3DXWARE_SUPPORT
	enable3DMouse(true);
#else
	ui.actionEnable3DMouse->setEnabled(false);
#endif

	// Signals & slots connection
	connect(m_glWindow->signalEmitter(), &ccGLWindowSignalEmitter::filesDropped, this, qOverload<QStringList>(&ccViewer::addToDB), Qt::QueuedConnection);
	connect(m_glWindow->signalEmitter(), &ccGLWindowSignalEmitter::entitySelectionChanged, this, &ccViewer::selectEntity);

	//"Options" menu
	connect(ui.actionDisplayParameters, &QAction::triggered, this, &ccViewer::showDisplayParameters);
	connect(ui.actionEditCamera, &QAction::triggered, this, &ccViewer::doActionEditCamera);
	//"Display > Standard views" menu
	connect(ui.actionSetViewTop, &QAction::triggered, this, &ccViewer::setTopView);
	connect(ui.actionSetViewBottom, &QAction::triggered, this, &ccViewer::setBottomView);
	connect(ui.actionSetViewFront, &QAction::triggered, this, &ccViewer::setFrontView);
	connect(ui.actionSetViewBack, &QAction::triggered, this, &ccViewer::setBackView);
	connect(ui.actionSetViewLeft, &QAction::triggered, this, &ccViewer::setLeftView);
	connect(ui.actionSetViewRight, &QAction::triggered, this, &ccViewer::setRightView);
	connect(ui.actionSetViewIso1, &QAction::triggered, this, &ccViewer::setIsoView1);
	connect(ui.actionSetViewIso2, &QAction::triggered, this, &ccViewer::setIsoView2);
	//"Options > Perspective" menu
	connect(ui.actionSetOrthoView, &QAction::triggered, this, &ccViewer::setOrthoView);
	connect(ui.actionSetCenteredPerspectiveView, &QAction::triggered, this, &ccViewer::setCenteredPerspectiveView);
	connect(ui.actionSetViewerPerspectiveView, &QAction::triggered, this, &ccViewer::setViewerPerspectiveView);
	connect(ui.actionSetPivotAlwaysOn, &QAction::triggered, this, &ccViewer::setPivotAlwaysOn);
	connect(ui.actionSetPivotRotationOnly, &QAction::triggered, this, &ccViewer::setPivotRotationOnly);
	connect(ui.actionSetPivotOff, &QAction::triggered, this, &ccViewer::setPivotOff);
	connect(ui.actionEnable3DMouse, &QAction::toggled, this, &ccViewer::enable3DMouse);
	connect(ui.actionToggleSunLight, &QAction::toggled, this, &ccViewer::toggleSunLight);
	connect(ui.actionToggleCustomLight, &QAction::toggled, this, &ccViewer::toggleCustomLight);
	connect(ui.actionGlobalZoom, &QAction::triggered, this, &ccViewer::setGlobalZoom);
	connect(ui.actionEnableStereo, &QAction::toggled, this, &ccViewer::toggleStereoMode);
	connect(ui.actionFullScreen, &QAction::toggled, this, &ccViewer::toggleFullScreen);
	connect(ui.actionLockRotationVertAxis, &QAction::triggered, this, &ccViewer::toggleRotationAboutVertAxis);
	connect(ui.actionShowColors, &QAction::toggled, this, &ccViewer::toggleColorsShown);
	connect(ui.actionShowNormals, &QAction::toggled, this, &ccViewer::toggleNormalsShown);
	connect(ui.actionShowMaterials, &QAction::toggled, this, &ccViewer::toggleMaterialsShown);
	connect(ui.actionShowScalarField, &QAction::toggled, this, &ccViewer::toggleScalarShown);
	connect(ui.actionShowColorRamp, &QAction::toggled, this, &ccViewer::toggleColorbarShown);
	connect(ui.actionZoomOnSelectedEntity, &QAction::triggered, this, &ccViewer::zoomOnSelectedEntity);
	connect(ui.actionDelete, &QAction::triggered, this, &ccViewer::doActionDeleteSelectedEntity);
	connect(ui.actionNoFilter, &QAction::triggered, this, &ccViewer::doDisableGLFilter);
	connect(ui.actionAbout, &QAction::triggered, this, &ccViewer::doActionAbout);
	connect(ui.actionHelpShortcuts, &QAction::triggered, this, &ccViewer::doActionDisplayShortcuts);

	// Additional shortcuts
	{
		QShortcut* plusKey = new QShortcut(QKeySequence(tr("+", "Zoom in")), this);
		connect(plusKey, &QShortcut::activated, [this]() { m_glWindow->onWheelEvent(8.0); });

		QShortcut* minusKey = new QShortcut(QKeySequence(tr("=", "Zoom out")), this);
		connect(minusKey, &QShortcut::activated, [this]() { m_glWindow->onWheelEvent(-8.0); });

		QShortcut* shiftUpKey = new QShortcut(QKeySequence(Qt::SHIFT | Qt::Key_Up), this);
		connect(shiftUpKey, &QShortcut::activated, [this]() { selectNextSF(-1); });

		QShortcut* shiftDownKey = new QShortcut(QKeySequence(Qt::SHIFT | Qt::Key_Down), this);
		connect(shiftDownKey, &QShortcut::activated, [this]() { selectNextSF(1); });
	}

	loadPlugins();
	loadStandardPlugins();
}

ccViewer::~ccViewer()
{
	release3DMouse();

	if (s_cpeDlg) { delete s_cpeDlg; s_cpeDlg = nullptr; }

	// === SLIM: Clipping box cleanup (owned by ccViewer, never by the DB) ===
	if (m_clipBox)
	{
		if (m_clipBoxActive)
		{
			closeClipBox();
		}
		delete m_clipBox;
		m_clipBox = nullptr;
	}

	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (currentRoot) { m_glWindow->setSceneDB(nullptr); delete currentRoot; }
}

void ccViewer::loadPlugins()
{
	ui.menuPlugins->setEnabled(false);
	ccPluginManager::Get().loadPlugins();

	for (ccPluginInterface* plugin : ccPluginManager::Get().pluginList())
	{
		if (plugin == nullptr) continue;

		if (plugin->getType() == CC_GL_FILTER_PLUGIN)
		{
			ccGLPluginInterface* glPlugin = static_cast<ccGLPluginInterface*>(plugin);
			const QString pluginName = glPlugin->getName();
			if (pluginName.isEmpty()) continue;

			ccLog::Print(QStringLiteral("Plugin name: [%1] (GL filter)").arg(pluginName));
			QAction* action = new QAction(pluginName, this);
			action->setToolTip(glPlugin->getDescription());
			action->setIcon(glPlugin->getIcon());
			QVariant v; v.setValue(glPlugin);
			action->setData(v);
			connect(action, &QAction::triggered, this, &ccViewer::doEnableGLFilter);
			ui.menuPlugins->addAction(action);
			ui.menuPlugins->setEnabled(true);
			ui.menuPlugins->setVisible(true);
		}
	}
}

// === SLIM: Standard plugin loading (Python/MATLAB extension point) ===
void ccViewer::loadStandardPlugins()
{
	for (ccPluginInterface* plugin : ccPluginManager::Get().pluginList())
	{
		if (plugin == nullptr) continue;
		if (plugin->getType() == CC_STD_PLUGIN)
		{
			ccStdPluginInterface* stdPlugin = static_cast<ccStdPluginInterface*>(plugin);
			stdPlugin->setMainAppInterface(this);
			ccLog::Print(QStringLiteral("Standard plugin loaded: [%1]").arg(stdPlugin->getName()));
			const QList<QAction*>& actions = stdPlugin->getActions();
			for (QAction* action : actions)
				ui.menuPlugins->addAction(action);
			if (!actions.isEmpty()) { ui.menuPlugins->setEnabled(true); ui.menuPlugins->setVisible(true); }
		}
	}
}

void ccViewer::doDisableGLFilter()
{
	if (m_glWindow) { m_glWindow->setGlFilter(nullptr); m_glWindow->redraw(); }
}

void ccViewer::doEnableGLFilter()
{
	if (!m_glWindow) return;
	QAction* action = qobject_cast<QAction*>(sender());
	if (!action) return;
	ccGLPluginInterface* plugin = action->data().value<ccGLPluginInterface*>();
	if (!plugin) return;

	ccGlFilter* filter = plugin->getFilter();
	if (filter)
	{
		if (m_glWindow->areGLFiltersEnabled())
		{
			m_glWindow->setGlFilter(filter);
			ccLog::Print("Note: go to << Display > Shaders & Filters > No filter >> to disable GL filter");
		}
		else ccLog::Error("GL filters not supported");
	}
	else ccLog::Error("Can't load GL filter (an error occurred)!");
}

void ccViewer::doActionDeleteSelectedEntity()
{
	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (!currentRoot) return;

	// === SLIM: discard any active clipping session first (the target cloud may be deleted)
	if (m_clipBoxActive)
	{
		m_actionClipBox->blockSignals(true);
		m_actionClipBox->setChecked(false);
		m_actionClipBox->blockSignals(false);
		closeClipBox();
	}

	ccHObject::Container toCheck; toCheck.push_back(currentRoot);
	while (!toCheck.empty())
	{
		ccHObject* obj = toCheck.back(); toCheck.pop_back();
		if (obj->isSelected())
		{
			if (obj->getParent())
			{
				obj->getParent()->addDependency(obj, ccHObject::DP_DELETE_OTHER);
				obj->getParent()->removeChild(obj);
			}
			else { delete obj; obj = nullptr; }
		}
		else { for (unsigned i = 0; i < obj->getChildrenNumber(); ++i) toCheck.push_back(obj->getChild(i)); }
	}
	m_glWindow->redraw();
}

void ccViewer::selectEntity(ccHObject* toSelect)
{
	// === SLIM: while the clipping box tool is active, ignore any (mis)selection
	// of the box itself or of one of its parts
	if (m_clipBoxActive && m_clipBox && toSelect
	    && (toSelect == m_clipBox || m_clipBox->isAncestorOf(toSelect)))
	{
		return;
	}

	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (!currentRoot) return;

	currentRoot->setSelected_recursive(false);
	ui.menuSelectSF->clear();
	ui.menuSelected->setEnabled(false);
	m_selectedEntities.clear();

	if (toSelect)
	{
		toSelect->setSelected(true);
		m_selectedEntities.push_back(toSelect);

		ui.actionShowColors->blockSignals(true);
		ui.actionShowNormals->blockSignals(true);
		ui.actionShowMaterials->blockSignals(true);
		ui.actionShowScalarField->blockSignals(true);
		ui.actionShowColorRamp->blockSignals(true);

		ui.actionShowColors->setEnabled(toSelect->hasColors());
		ui.actionShowColors->setChecked(toSelect->colorsShown());
		ui.actionShowNormals->setEnabled(toSelect->hasNormals());
		ui.actionShowNormals->setChecked(toSelect->normalsShown());

		if (toSelect->isKindOf(CC_TYPES::MESH))
		{
			ccGenericMesh* mesh = static_cast<ccGenericMesh*>(toSelect);
			ui.actionShowMaterials->setEnabled(mesh->hasMaterials());
			ui.actionShowMaterials->setChecked(mesh->materialsShown());
		}
		else { ui.actionShowMaterials->setEnabled(false); ui.actionShowMaterials->setChecked(false); }

		ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(toSelect);
		bool hasSF = (cloud ? cloud->hasScalarFields() : false);
		ui.actionShowScalarField->setEnabled(hasSF);
		ui.actionShowScalarField->setChecked(toSelect->sfShown());
		ui.actionShowColorRamp->setEnabled(hasSF);
		ui.actionShowColorRamp->setChecked(cloud ? cloud->sfColorScaleShown() && cloud->sfShown() : false);

		unsigned sfCount = (cloud ? cloud->getNumberOfScalarFields() : 0);
		ui.menuSelectSF->setEnabled(hasSF && sfCount > 1);
		if (hasSF && sfCount > 1)
		{
			int currentSFIndex = cloud->getCurrentDisplayedScalarFieldIndex();
			for (unsigned i = 0; i < sfCount; ++i)
			{
				QAction* action = ui.menuSelectSF->addAction(QString::fromStdString(cloud->getScalarFieldName(i)));
				action->setData(i);
				action->setCheckable(true);
				if (currentSFIndex == static_cast<int>(i)) action->setChecked(true);
				connect(action, &QAction::toggled, this, &ccViewer::changeCurrentScalarField);
			}
		}

		// === SLIM: Enable processing actions when entity selected ===
		bool isCloud = (cloud != nullptr);
		bool isMesh = toSelect->isKindOf(CC_TYPES::MESH);
		m_actionNormals->setEnabled(isCloud);
		m_actionSubsample->setEnabled(isCloud);
		m_actionFilterByValue->setEnabled(isCloud && hasSF);
		m_actionSORFilter->setEnabled(isCloud);

		// === SLIM: Enable tools actions when cloud selected ===
		// (keep 'Clip by Box' enabled while active so that the user can always close it)
		m_actionClipBox->setEnabled(isCloud || m_clipBoxActive);
		m_actionTLSPlane->setEnabled(isCloud);
		m_actionPointProjection->setEnabled(isCloud);
		m_actionKNN->setEnabled(isCloud);
		// Rotation Matrix does not require a cloud selection
		// === SLIM: Enable new native C++ tools on cloud selection ===
		m_actionBoundaryExtract->setEnabled(isCloud);
		m_actionFoldExtract->setEnabled(isCloud);
		m_actionSphereNeighborhood->setEnabled(isCloud);
		m_actionSpherePCA->setEnabled(isCloud);

		ui.menuSelected->setEnabled(true);

		ui.actionShowColors->blockSignals(false);
		ui.actionShowNormals->blockSignals(false);
		ui.actionShowMaterials->blockSignals(false);
		ui.actionShowScalarField->blockSignals(false);
		ui.actionShowColorRamp->blockSignals(false);

		m_selectedObject = toSelect;
	}
	m_glWindow->redraw();
}

bool ccViewer::checkForLoadedEntities()
{
	bool loadedEntities = true;
	m_glWindow->displayNewMessage(QString(), ccGLWindowInterface::SCREEN_CENTER_MESSAGE);
	if (!m_glWindow->getSceneDB())
	{
		m_glWindow->displayNewMessage("Drag & drop files on the 3D window to load them!", ccGLWindowInterface::SCREEN_CENTER_MESSAGE, true, 3600);
		loadedEntities = false;
	}
	if (m_glWindow->getDisplayParameters().displayCross != loadedEntities)
	{
		ccGui::ParamStruct params = m_glWindow->getDisplayParameters();
		params.displayCross = loadedEntities;
		m_glWindow->setDisplayParameters(params);
	}
	return loadedEntities;
}

void ccViewer::updateDisplay() { updateGLFrameGradient(); m_glWindow->redraw(); }

void ccViewer::updateGLFrameGradient()
{
	static const ccColor::Rgbub s_black(0, 0, 0);
	static const ccColor::Rgbub s_white(255, 255, 255);
	bool stereoModeEnabled = m_glWindow->stereoModeIsEnabled();
	const ccColor::Rgbub& bkgCol = stereoModeEnabled ? s_black : m_glWindow->getDisplayParameters().backgroundCol;
	const ccColor::Rgbub& forCol = stereoModeEnabled ? s_white : m_glWindow->getDisplayParameters().pointsDefaultCol;
	QString styleSheet = QString("QFrame#GLframe{border: 2px solid white; border-radius: 10px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1,stop:0 rgb(%1,%2,%3), stop:1 rgb(%4,%5,%6));}")
	                         .arg(bkgCol.r).arg(bkgCol.g).arg(bkgCol.b)
	                         .arg(255 - forCol.r).arg(255 - forCol.g).arg(255 - forCol.b);
	ui.GLframe->setStyleSheet(styleSheet);
}

ccHObject* ccViewer::addToDB(QStringList filenames)
{
	// === SLIM: discard any active clipping session (the whole DB is about to be replaced)
	if (m_clipBoxActive)
	{
		m_actionClipBox->blockSignals(true);
		m_actionClipBox->setChecked(false);
		m_actionClipBox->blockSignals(false);
		closeClipBox();
	}

	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (currentRoot)
	{
		m_selectedObject = nullptr;
		m_selectedEntities.clear();
		m_glWindow->setSceneDB(nullptr);
		m_glWindow->redraw();
		delete currentRoot;
		currentRoot = nullptr;
	}

	bool scaleAlreadyDisplayed = false;
	FileIOFilter::LoadParameters parameters;
	parameters.alwaysDisplayLoadDialog = false;
	parameters.shiftHandlingMode = ccGlobalShiftManager::NO_DIALOG_AUTO_SHIFT;
	parameters.parentWidget = this;
	const ccOptions& options = ccOptions::Instance();
	FileIOFilter::ResetSesionCounter();
	ccHObject* firstLoadedEntity = nullptr;

	for (int i = 0; i < filenames.size(); ++i)
	{
		CC_FILE_ERROR result = CC_FERR_NO_ERROR;
		ccHObject* newGroup = FileIOFilter::LoadFromFile(filenames[i], parameters, result);

		if (newGroup)
		{
			if (!options.normalsDisplayedByDefault)
			{
				ccHObject::Container clouds;
				newGroup->filterChildren(clouds, true, CC_TYPES::POINT_CLOUD);
				for (ccHObject* cloud : clouds)
				{
					if (cloud)
					{
						static_cast<ccGenericPointCloud*>(cloud)->showNormals(false);
					}
				}
			}

			addToDB(newGroup);

			if (!scaleAlreadyDisplayed)
			{
				for (unsigned j = 0; j < newGroup->getChildrenNumber(); ++j)
				{
					ccHObject* ent = newGroup->getChild(j);
					if (ent->isA(CC_TYPES::POINT_CLOUD))
					{
						ccPointCloud* pc = static_cast<ccPointCloud*>(ent);
						if (pc->hasScalarFields())
						{
							pc->setCurrentDisplayedScalarField(0);
							pc->showSFColorsScale(true);
							scaleAlreadyDisplayed = true;
						}
					}
					else if (ent->isKindOf(CC_TYPES::MESH))
					{
						ccGenericMesh* mesh = static_cast<ccGenericMesh*>(ent);
						if (mesh->hasScalarFields())
						{
							mesh->showSF(true);
							scaleAlreadyDisplayed = true;
							static_cast<ccPointCloud*>(mesh->getAssociatedCloud())->showSFColorsScale(true);
						}
					}
				}
			}
			if (!firstLoadedEntity)
			{
				firstLoadedEntity = newGroup;
			}
		}
		if (!newGroup && result != CC_FERR_NO_ERROR && result != CC_FERR_CANCELED_BY_USER)
		{
			FileIOFilter::DisplayErrorMessage(result, "loading", filenames[i]);
		}
		if (result == CC_FERR_CANCELED_BY_USER)
		{
			break;
		}
	}
	checkForLoadedEntities();
	return firstLoadedEntity;
}

void ccViewer::addToDB(ccHObject* entity, bool updateZoom, bool autoExpandDBTree, bool checkDimensions, bool autoRedraw)
{
	assert(entity && m_glWindow);
	entity->setDisplay_recursive(m_glWindow);
	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (currentRoot)
	{
		if (currentRoot->isA(CC_TYPES::HIERARCHY_OBJECT)) currentRoot->addChild(entity);
		else
		{
			ccHObject* root = new ccHObject("root");
			root->addChild(currentRoot);
			root->addChild(entity);
			m_glWindow->setSceneDB(root);
		}
	}
	else m_glWindow->setSceneDB(entity);
	checkForLoadedEntities();
}

void ccViewer::removeFromDB(ccHObject* obj, bool autoDelete)
{
	ccHObject* currentRoot = m_glWindow->getSceneDB();
	if (currentRoot)
	{
		if (currentRoot == obj) { m_glWindow->setSceneDB(nullptr); if (autoDelete) delete currentRoot; }
		else currentRoot->removeChild(obj);
	}
	m_glWindow->redraw();
}

void ccViewer::showDisplayParameters()
{
	ccDisplaySettingsDlg clmDlg(this);
	connect(&clmDlg, &ccDisplaySettingsDlg::aspectHasChanged, this, &ccViewer::updateDisplay);
	clmDlg.exec();
	disconnect(&clmDlg, nullptr, nullptr, nullptr);
}

void ccViewer::doActionEditCamera()
{
	if (!s_cpeDlg) { s_cpeDlg = new ccCameraParamEditDlg(this, nullptr); s_cpeDlg->linkWith(m_glWindow); }
	s_cpeDlg->show();
}

void ccViewer::reflectPerspectiveState()
{
	if (!m_glWindow) return;
	bool objectCentered = false;
	bool perspectiveEnabled = m_glWindow->getPerspectiveState(objectCentered);
	ui.actionSetOrthoView->setChecked(!perspectiveEnabled);
	ui.actionSetCenteredPerspectiveView->setChecked(perspectiveEnabled && objectCentered);
	ui.actionSetViewerPerspectiveView->setChecked(perspectiveEnabled && !objectCentered);
}

bool ccViewer::checkStereoMode()
{
	if (m_glWindow && m_glWindow->getViewportParameters().perspectiveView && m_glWindow->stereoModeIsEnabled())
	{
		if (QMessageBox::question(this, "Stereo mode", "Stereo-mode only works in perspective mode. Do you want to enable it?", QMessageBox::Yes, QMessageBox::No) == QMessageBox::No) return false;
		else toggleStereoMode(false);
	}
	return true;
}

void ccViewer::setOrthoView()
{
	if (m_glWindow)
	{
		if (!checkStereoMode()) return;
		m_glWindow->setPerspectiveState(false, true);
		m_glWindow->redraw();
	}
	reflectPerspectiveState();
}

void ccViewer::setCenteredPerspectiveView()
{
	if (m_glWindow) { m_glWindow->setPerspectiveState(true, true); m_glWindow->redraw(); }
	reflectPerspectiveState();
}

void ccViewer::setViewerPerspectiveView()
{
	if (m_glWindow) { m_glWindow->setPerspectiveState(true, false); m_glWindow->redraw(); }
	reflectPerspectiveState();
}

void ccViewer::reflectPivotVisibilityState()
{
	if (!m_glWindow) return;
	ccGLWindowInterface::PivotVisibility vis = m_glWindow->getPivotVisibility();
	ui.actionSetPivotAlwaysOn->setChecked(vis == ccGLWindowInterface::PIVOT_ALWAYS_SHOW);
	ui.actionSetPivotRotationOnly->setChecked(vis == ccGLWindowInterface::PIVOT_SHOW_ON_MOVE);
	ui.actionSetPivotOff->setChecked(vis == ccGLWindowInterface::PIVOT_HIDE);
}

void ccViewer::setPivotAlwaysOn()
{
	if (m_glWindow) { m_glWindow->setPivotVisibility(ccGLWindowInterface::PIVOT_ALWAYS_SHOW); m_glWindow->redraw(); }
	reflectPivotVisibilityState();
}

void ccViewer::setPivotRotationOnly()
{
	if (m_glWindow) { m_glWindow->setPivotVisibility(ccGLWindowInterface::PIVOT_SHOW_ON_MOVE); m_glWindow->redraw(); }
	reflectPivotVisibilityState();
}

void ccViewer::setPivotOff()
{
	if (m_glWindow) { m_glWindow->setPivotVisibility(ccGLWindowInterface::PIVOT_HIDE); m_glWindow->redraw(); }
	reflectPivotVisibilityState();
}

void ccViewer::reflectLightsState()
{
	if (!m_glWindow) return;
	ui.actionToggleSunLight->blockSignals(true);
	ui.actionToggleCustomLight->blockSignals(true);
	ui.actionToggleSunLight->setChecked(m_glWindow->sunLightEnabled());
	ui.actionToggleCustomLight->setChecked(m_glWindow->customLightEnabled());
	ui.actionToggleSunLight->blockSignals(false);
	ui.actionToggleCustomLight->blockSignals(false);
}

void ccViewer::toggleSunLight(bool state) { if (m_glWindow) m_glWindow->setSunLight(state); reflectLightsState(); }
void ccViewer::toggleCustomLight(bool state) { if (m_glWindow) m_glWindow->setCustomLight(state); reflectLightsState(); }

void ccViewer::toggleStereoMode(bool state)
{
	if (!m_glWindow) return;
	bool isActive = m_glWindow->stereoModeIsEnabled();
	if (isActive == state) return;

	if (isActive)
	{
		m_glWindow->disableStereoMode();
		if (m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::NVIDIA_VISION
		    || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::GENERIC_STEREO_DISPLAY
		    || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::SIDE_BY_SIDE)
			ui.actionFullScreen->setChecked(false);
	}
	else
	{
		ccStereoModeDlg smDlg(this);
		smDlg.setParameters(m_glWindow->getStereoParams());
		if (!smDlg.exec())
		{
			ui.actionEnableStereo->blockSignals(true);
			ui.actionEnableStereo->setChecked(false);
			ui.actionEnableStereo->blockSignals(false);
			return;
		}
		ccGLWindowInterface::StereoParams params = smDlg.getParameters();
		if (params.quadBufferingRequired() && !ccGLWindowInterface::StereoSupported())
		{
			ccLog::Error(tr("Your graphic card doesn't support Quad Buffered Stereo"));
			ui.actionEnableStereo->blockSignals(true);
			ui.actionEnableStereo->setChecked(false);
			ui.actionEnableStereo->blockSignals(false);
			return;
		}
		if (!m_glWindow->getViewportParameters().perspectiveView) { m_glWindow->setPerspectiveState(true, true); reflectPerspectiveState(); }
		if (params.glassType == ccGLWindowInterface::StereoParams::NVIDIA_VISION
		    || params.glassType == ccGLWindowInterface::StereoParams::GENERIC_STEREO_DISPLAY
		    || params.glassType == ccGLWindowInterface::StereoParams::SIDE_BY_SIDE)
			ui.actionFullScreen->setChecked(true);
		if (!m_glWindow->enableStereoMode(params))
		{
			ui.actionEnableStereo->blockSignals(true);
			ui.actionEnableStereo->setChecked(false);
			ui.actionEnableStereo->blockSignals(false);
		}
	}
	updateDisplay();
}

void ccViewer::toggleFullScreen(bool state)
{
	if (m_glWindow)
	{
		if (m_glWindow->stereoModeIsEnabled() && (m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::NVIDIA_VISION || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::GENERIC_STEREO_DISPLAY || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::SIDE_BY_SIDE))
			ui.actionEnableStereo->setChecked(false);
		m_glWindow->toggleExclusiveFullScreen(state);
	}
}

void ccViewer::onExclusiveFullScreenToggled(bool state)
{
	ui.actionFullScreen->blockSignals(true);
	ui.actionFullScreen->setChecked(m_glWindow ? m_glWindow->exclusiveFullScreen() : false);
	ui.actionFullScreen->blockSignals(false);
	if (!state && m_glWindow && m_glWindow->stereoModeIsEnabled() && (m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::NVIDIA_VISION || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::GENERIC_STEREO_DISPLAY || m_glWindow->getStereoParams().glassType == ccGLWindowInterface::StereoParams::SIDE_BY_SIDE))
		ui.actionEnableStereo->setChecked(false);
}

void ccViewer::toggleRotationAboutVertAxis()
{
	if (!m_glWindow) return;
	bool wasLocked = m_glWindow->isRotationAxisLocked();
	bool isLocked = !wasLocked;
	m_glWindow->lockRotationAxis(isLocked, CCVector3d(0.0, 0.0, 1.0));
	ui.actionLockRotationVertAxis->blockSignals(true);
	ui.actionLockRotationVertAxis->setChecked(isLocked);
	ui.actionLockRotationVertAxis->blockSignals(false);
	if (isLocked) m_glWindow->displayNewMessage(QString("[ROTATION LOCKED]"), ccGLWindowInterface::UPPER_CENTER_MESSAGE, false, 24 * 3600, ccGLWindowInterface::ROTAION_LOCK_MESSAGE);
	else m_glWindow->displayNewMessage(QString(), ccGLWindowInterface::UPPER_CENTER_MESSAGE, false, 0, ccGLWindowInterface::ROTAION_LOCK_MESSAGE);
	m_glWindow->redraw();
}

void ccViewer::doActionDisplayShortcuts()
{
	QString text;
	text += "Shortcuts:\n\n";
	text += "F2 : Set orthographic view\n";
	text += "F3 : Set object-centered perspective\n";
	text += "F4 : Set viewer-based perspective\n";
	text += "F6 : Toggle sun light\n";
	text += "F7 : Toggle custom light\n";
	text += "F11: Toggle exclusive full screen\n";
	text += "+  : Zoom in\n";
	text += "=  : Zoom out\n";
	text += "0,2,4-9: Set default camera orientation\n";
	text += "DEL: Delete entity\n";
	QMessageBox msgBox; msgBox.setText(text); msgBox.exec();
}

void ccViewer::setTopView()    { m_glWindow->setView(CC_TOP_VIEW); }
void ccViewer::setBottomView() { m_glWindow->setView(CC_BOTTOM_VIEW); }
void ccViewer::setFrontView()  { m_glWindow->setView(CC_FRONT_VIEW); }
void ccViewer::setBackView()   { m_glWindow->setView(CC_BACK_VIEW); }
void ccViewer::setLeftView()   { m_glWindow->setView(CC_LEFT_VIEW); }
void ccViewer::setRightView()  { m_glWindow->setView(CC_RIGHT_VIEW); }
void ccViewer::setIsoView1()   { m_glWindow->setView(CC_ISO_VIEW_1); }
void ccViewer::setIsoView2()   { m_glWindow->setView(CC_ISO_VIEW_2); }

void ccViewer::toggleColorsShown(bool state) { if (m_selectedObject) { m_selectedObject->showColors(state); m_glWindow->redraw(); } }
void ccViewer::toggleNormalsShown(bool state) { if (m_selectedObject) { m_selectedObject->showNormals(state); m_glWindow->redraw(); } }
void ccViewer::toggleMaterialsShown(bool state) { if (m_selectedObject && m_selectedObject->isKindOf(CC_TYPES::MESH)) { static_cast<ccGenericMesh*>(m_selectedObject)->showMaterials(state); m_glWindow->redraw(); } }
void ccViewer::toggleScalarShown(bool state) { if (m_selectedObject) { m_selectedObject->showSF(state); m_glWindow->redraw(); } }

void ccViewer::toggleColorbarShown(bool state)
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (cloud) { cloud->showSFColorsScale(state); m_glWindow->redraw(true, false); }
}

void ccViewer::changeCurrentScalarField(bool state)
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) return;
	QAction* action = qobject_cast<QAction*>(QObject::sender());
	if (!action) return;
	const QObjectList& children = ui.menuSelectSF->children();
	for (int i = 0; i < children.size(); ++i) { QAction* act = static_cast<QAction*>(children[i]); act->blockSignals(true); act->setChecked(act == action); act->blockSignals(false); }
	int sfIndex = action->data().toInt();
	if (sfIndex < static_cast<int>(cloud->getNumberOfScalarFields()))
	{
		cloud->setCurrentDisplayedScalarField(sfIndex);
		ui.actionShowScalarField->blockSignals(true);
		ui.actionShowScalarField->setChecked(true);
		ui.actionShowScalarField->blockSignals(false);
		m_glWindow->redraw();
	}
}

void ccViewer::setGlobalZoom() { if (m_glWindow) m_glWindow->zoomGlobal(); }

void ccViewer::zoomOnSelectedEntity()
{
	if (!m_glWindow || !m_selectedObject) return;
	ccBBox box = m_selectedObject->getDisplayBB_recursive(false, m_glWindow);
	m_glWindow->updateConstellationCenterAndZoom(&box);
	m_glWindow->redraw();
}

#include <ui_ccviewerAbout.h>
void ccViewer::doActionAbout()
{
	QDialog aboutDialog(this);
	Ui::AboutDialog ui;
	ui.setupUi(&aboutDialog);
	ui.textEdit->setHtml(ui.textEdit->toHtml().arg(ccApp->versionLongStr(true)));
	aboutDialog.exec();
}

// ============================================================================
// SLIM: Point cloud processing slot implementations
// ============================================================================

void ccViewer::doActionComputeNormals()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	ccNormalComputationDlg dlg(false, false, this);
	dlg.setCloud(cloud);
	if (dlg.exec() == QDialog::Accepted)
	{
		ccProgressDialog progressDlg(true, this);
		progressDlg.setAutoClose(false);

		bool ok = false;
		if (dlg.useScanGridsForComputation() && cloud->computeNormalsWithGrids(dlg.getMinGridAngle_deg(), &progressDlg, dlg.getPreferredOrientation()))
		{
			ok = true;
		}
		else
		{
			ok = cloud->computeNormalsWithOctree(dlg.getLocalModel(), dlg.getPreferredOrientation(), dlg.getRadius(), &progressDlg);
		}

		if (ok)
		{
			if (dlg.orientNormals())
			{
				if (dlg.useMSTOrientation())
				{
					cloud->orientNormalsWithMST(dlg.getMSTNeighborCount(), &progressDlg);
				}
				else if (dlg.usePreferredOrientation())
				{
					cloud->showNormalsAsLines(true);
				}
			}

			cloud->showNormalsAsLines(true);
			cloud->setEnabled(true);
			m_glWindow->redraw();
			ccLog::Print("[Normals] Computation finished");
		}
		else
		{
			ccLog::Error("[Normals] Computation failed");
		}
	}
}

void ccViewer::doActionSubsample()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }
	double maxRadius = cloud->getOwnBB().getDiagNorm();
	ccSubsamplingDlg dlg(cloud->size(), maxRadius, this);
	if (dlg.exec() == QDialog::Accepted)
	{
		CCCoreLib::ReferenceCloud* sampled = dlg.getSampledCloud(cloud);
		if (sampled && sampled->size() > 0)
		{
			ccPointCloud* newCloud = cloud->partialClone(sampled);
			if (newCloud)
			{
				newCloud->setName(cloud->getName() + QString(".subsampled"));
				addToDB(newCloud, true, true, false, true);
				ccLog::Print(QString("[Subsample] %1 points").arg(newCloud->size()));
			}
		}
	}
}

void ccViewer::doActionFilterByValue()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud || !cloud->hasScalarFields()) { ccLog::Error("Select a point cloud with scalar fields first"); return; }
	int sfIdx = cloud->getCurrentDisplayedScalarFieldIndex();
	if (sfIdx < 0) sfIdx = 0;
	CCCoreLib::ScalarField* sf = cloud->getScalarField(sfIdx);
	if (!sf) return;
	sf->computeMinAndMax();
	ccFilterByValueDlg dlg(sf->getMin(), sf->getMax(), sf->getMin(), sf->getMax(), this);
	if (dlg.exec() == QDialog::Accepted && dlg.mode() != ccFilterByValueDlg::CANCEL)
	{
		double minVal = dlg.minDoubleSpinBox->value();
		double maxVal = dlg.maxDoubleSpinBox->value();
		cloud->setCurrentScalarField(sfIdx);
		unsigned n = cloud->size();

		if (dlg.mode() == ccFilterByValueDlg::SPLIT)
		{
			CCCoreLib::ReferenceCloud insideRef(cloud);
			CCCoreLib::ReferenceCloud outsideRef(cloud);
			for (unsigned i = 0; i < n; ++i)
			{
				const ScalarType val = sf->getValue(i);
				if (val >= minVal && val <= maxVal)
					insideRef.addPointIndex(i);
				else
					outsideRef.addPointIndex(i);
			}

			if (insideRef.size() > 0)
			{
				ccPointCloud* insideCloud = cloud->partialClone(&insideRef);
				if (insideCloud)
				{
					insideCloud->setName(cloud->getName() + QString(".inside"));
					addToDB(insideCloud, true, true, false, true);
				}
			}
			if (outsideRef.size() > 0)
			{
				ccPointCloud* outsideCloud = cloud->partialClone(&outsideRef);
				if (outsideCloud)
				{
					outsideCloud->setName(cloud->getName() + QString(".outside"));
					addToDB(outsideCloud, true, true, false, true);
				}
			}

			ccLog::Print(QString("[Filter by Value] Split: min=%1, max=%2").arg(minVal).arg(maxVal));
		}
		else if (dlg.mode() == ccFilterByValueDlg::EXPORT)
		{
			CCCoreLib::ReferenceCloud exportedRef(cloud);
			for (unsigned i = 0; i < n; ++i)
			{
				const ScalarType val = sf->getValue(i);
				if (val >= minVal && val <= maxVal)
					exportedRef.addPointIndex(i);
			}

			if (exportedRef.size() > 0)
			{
				ccPointCloud* newCloud = cloud->partialClone(&exportedRef);
				if (newCloud)
				{
					newCloud->setName(cloud->getName() + QString(".exported"));
					addToDB(newCloud, true, true, false, true);
					ccLog::Print(QString("[Filter by Value] Exported %1 points (range: %2-%3)").arg(newCloud->size()).arg(minVal).arg(maxVal));
				}
			}
		}
	}
}

void ccViewer::doActionSORFilter()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	ccSORFilterDlg dlg(this);
	if (dlg.exec() == QDialog::Accepted)
	{
		int    knn    = dlg.KNN();
		double nSigma = dlg.nSigma();

		// Perform Statistical Outlier Removal using CCCoreLib
		CCCoreLib::ReferenceCloud* filteredIndices =
		    CCCoreLib::CloudSamplingTools::sorFilter(cloud, knn, nSigma);

		if (!filteredIndices || filteredIndices->size() == 0)
		{
			ccLog::Error("[SOR Filter] No points survived filtering (all points are outliers?)");
			delete filteredIndices;
			return;
		}

		if (static_cast<int>(filteredIndices->size()) == cloud->size())
		{
			ccLog::Warning("[SOR Filter] All points passed — no outliers detected");
			delete filteredIndices;
			return;
		}

		// Create new cloud with the filtered points
		bool    autoAddChild = false;
		ccPointCloud* newCloud = cloud->partialClone(filteredIndices, nullptr, autoAddChild);
		delete filteredIndices;

		if (!newCloud)
		{
			ccLog::Error("[SOR Filter] Failed to create filtered cloud");
			return;
		}

		newCloud->setName(cloud->getName() + ".SOR");
		newCloud->setDisplay(cloud->getDisplay());

		// Add to DB and hide original
		addToDB(newCloud);
		cloud->setEnabled(false);
		cloud->setVisible(false);
		refreshAll();

		ccLog::Print(QString("[SOR Filter] %1/%2 points kept (KNN=%3, nSigma=%4)")
		                 .arg(newCloud->size())
		                 .arg(cloud->size())
		                 .arg(knn)
		                 .arg(nSigma));
	}
}


// ============================================================================
// SLIM: Tools menu - Clipping Box
// ============================================================================

void ccViewer::doActionClipBox()
{
	bool activate = m_actionClipBox->isChecked();

	if (activate)
	{
		ccPointCloud* cloud = m_selectedObject ? ccHObjectCaster::ToPointCloud(m_selectedObject) : nullptr;
		if (!cloud)
		{
			ccLog::Error("Select a point cloud first");
			m_actionClipBox->blockSignals(true);
			m_actionClipBox->setChecked(false);
			m_actionClipBox->blockSignals(false);
			return;
		}

		// Create the clipping box once and reuse it afterwards
		if (!m_clipBox)
		{
			m_clipBox = new ccClipBox("Clipping box");
			connect(m_clipBox, &ccClipBox::boxModified, this, &ccViewer::onClipBoxModified);
		}

		// Associate the cloud first (this resets the box), then size the box
		// to the cloud bounding box with some padding
		m_clipBox->addAssociatedEntity(cloud);

		ccBBox cloudBB = cloud->getOwnBB();
		CCVector3 padding = cloudBB.getDiagVec() * static_cast<PointCoordinateType>(0.05);
		ccBBox paddedBB(
			cloudBB.minCorner() - padding,
			cloudBB.maxCorner() + padding,
			true
		);

		m_clipBox->resetGLTransformation();
		m_clipBox->setBox(paddedBB);
		m_clipBox->setVisible(true);
		m_clipBox->showBox(true);
		m_clipBox->setEnabled(true);
		// the box must be 'selected' for its arrows/toruses to be drawn and pickable
		// (see ccClipBox::drawMeOnly which returns early when not selected)
		m_clipBox->setSelected(true);

		// Add to the GL window own DB *without* ownership transfer:
		// the box must never be deleted by the DB (see closeClipBox)
		m_glWindow->addToOwnDB(m_clipBox); // noDependency = true

		m_clipBoxCloud = cloud;
		m_clipBoxActive = true;
		m_glWindow->redraw();

		ccLog::Print("[Clip Box] Drag the box arrows to adjust the clipping region. Uncheck 'Clip by Box' to apply and remove.");
	}
	else
	{
		// Deactivate clipping box
		if (!m_clipBox || !m_clipBoxActive)
		{
			return;
		}

		// Ask user: apply clipping or discard?
		QMessageBox msgBox(this);
		msgBox.setWindowTitle(tr("Clip Box"));
		msgBox.setText(tr("Apply the clipping to create a cropped point cloud?"));
		msgBox.setInformativeText(tr("'Keep Inside' = crop and keep inside points\n'Keep Outside' = crop and keep outside points\n'Cancel' = discard clipping"));
		QPushButton* insideBtn = msgBox.addButton(tr("Keep Inside"), QMessageBox::YesRole);
		QPushButton* outsideBtn = msgBox.addButton(tr("Keep Outside"), QMessageBox::NoRole);
		QPushButton* cancelBtn = msgBox.addButton(tr("Cancel"), QMessageBox::RejectRole);
		msgBox.setDefaultButton(cancelBtn);
		msgBox.exec();

		bool keepInside = false;
		if (msgBox.clickedButton() == insideBtn)
		{
			keepInside = true;
		}
		else if (msgBox.clickedButton() == outsideBtn)
		{
			keepInside = false;
		}
		else
		{
			// Cancel - discard clipping
			closeClipBox();
			return;
		}

		// Apply the clipping on the cloud the box was activated on
		// (the current selection may have changed in the meantime)
		ccPointCloud* cloud = m_clipBoxCloud;
		if (cloud)
		{
			// Create visibility table and flag points
			ccGenericPointCloud::VisibilityTableType visTable(cloud->size());
			m_clipBox->flagPointsInside(cloud, &visTable, false);

			// Invert visibility if the user wants to keep the outside points
			unsigned keptCount = 0;
			for (unsigned i = 0; i < cloud->size(); ++i)
			{
				bool isInside = (visTable[i] == CCCoreLib::POINT_VISIBLE);
				bool keep = (keepInside == isInside);
				visTable[i] = keep ? CCCoreLib::POINT_VISIBLE : CCCoreLib::POINT_HIDDEN;
				if (keep)
				{
					++keptCount;
				}
			}

			if (keptCount > 0 && keptCount < cloud->size())
			{
				ccGenericPointCloud* newCloud = cloud->createNewCloudFromVisibilitySelection(false, &visTable);
				if (newCloud)
				{
					QString suffix = keepInside ? ".inside" : ".outside";
					newCloud->setName(cloud->getName() + suffix);
					addToDB(newCloud, true, true, false, true);

					// hide the original cloud so that the cropped result is
					// immediately visible (they would fully overlap otherwise)
					cloud->setVisible(false);

					ccLog::Print(QString("[Clip Box] Created cropped cloud: %1 points (original cloud hidden)").arg(newCloud->size()));

					// make the cropped cloud the current selection
					closeClipBox();
					selectEntity(newCloud);
					return;
				}
			}
			else
			{
				QMessageBox::information(this, tr("Clip Box"),
					keptCount == 0
						? tr("No points would remain: the %1 region is empty.").arg(keepInside ? tr("inside") : tr("outside"))
						: tr("All points would remain: the box does not exclude anything.\nDrag the box arrows to shrink the clipping region first."));
			}
		}

		closeClipBox();
	}
}

void ccViewer::closeClipBox()
{
	if (!m_clipBox)
	{
		return;
	}

	// remove the clipping planes from the associated cloud BEFORE
	// detaching the box from the display
	m_clipBox->releaseAssociatedEntities();
	m_glWindow->removeFromOwnDB(m_clipBox); // no dependency: detaches only, no delete
	m_clipBox->setSelected(false);
	m_clipBox->setVisible(false);

	m_clipBoxActive = false;
	m_clipBoxCloud = nullptr;
	m_glWindow->redraw();
}

void ccViewer::onClipBoxModified(const ccBBox* box)
{
	Q_UNUSED(box);
	if (!m_clipBox || !m_clipBoxActive)
	{
		return;
	}

	// The ccClipBox handles visual clipping internally via OpenGL clip planes
	// (see ccClipBox::update() which sets clip planes on associated entities).
	// We just need to redraw the scene.
	m_glWindow->redraw();
}

// ============================================================================
// SLIM: Tools menu - Python helper methods
// ============================================================================

QString ccViewer::pythonScriptsDir() const
{
	// Look for python/ directory next to the executable first, then in source tree
	QString exeDir = QCoreApplication::applicationDirPath();
	QString pythonDir = exeDir + "/python";
	if (QDir(pythonDir).exists())
		return pythonDir;

	// Fallback: look relative to the executable's parent (development layout)
	pythonDir = exeDir + "/../python";
	if (QDir(pythonDir).exists())
		return QDir(pythonDir).absolutePath();

	// Fallback: build tree layout (bin/ccViewer/ccViewer.exe -> ../../python)
	pythonDir = exeDir + "/../../python";
	if (QDir(pythonDir).exists())
		return QDir(pythonDir).absolutePath();

	return QString();
}

QString ccViewer::resolvePythonExe()
{
	if (!m_pythonExe.isEmpty())
	{
		return m_pythonExe;
	}

	QStringList candidates;

	// 1) explicit override
	QString envPython = qEnvironmentVariable("CCVIEWER_PYTHON");
	if (!envPython.isEmpty())
	{
		candidates << envPython;
	}

	// 2) python from PATH
	QString inPath = QStandardPaths::findExecutable("python");
	if (!inPath.isEmpty())
	{
		candidates << inPath;
	}

	// 3) Windows py launcher
	QString pyLauncher = QStandardPaths::findExecutable("py");
	if (!pyLauncher.isEmpty())
	{
		candidates << pyLauncher;
	}

	// 4) common per-user install locations (Python 3.x)
	QString localAppData = qEnvironmentVariable("LOCALAPPDATA");
	if (!localAppData.isEmpty())
	{
		QDir programsDir(localAppData + "/Programs/Python");
		const QStringList versions = programsDir.entryList(QStringList() << "Python3*", QDir::Dirs, QDir::Name | QDir::Reversed);
		for (const QString& version : versions)
		{
			candidates << programsDir.absoluteFilePath(version + "/python.exe");
		}
	}

	// validate the candidates: the Windows Store 'python.exe' stub (WindowsApps)
	// exits with an error, so a quick '--version' probe filters it out
	for (const QString& candidate : candidates)
	{
		QProcess probe;
		probe.start(candidate, QStringList() << "--version");
		if (probe.waitForStarted(3000) && probe.waitForFinished(5000) && probe.exitCode() == 0)
		{
			m_pythonExe = candidate;
			ccLog::Print(QString("[Python] Using interpreter: %1").arg(candidate));
			return m_pythonExe;
		}
	}

	ccLog::Error("No Python 3 interpreter found. Install Python (with numpy/scipy) or set the CCVIEWER_PYTHON environment variable to a python.exe path.");
	return QString();
}

QString ccViewer::runPythonScript(const QString& scriptName, const QStringList& args)
{
	QString scriptsDir = pythonScriptsDir();
	if (scriptsDir.isEmpty())
	{
		ccLog::Error("Python scripts directory not found (expected a 'python' folder next to the executable)");
		return QString();
	}

	QString scriptPath = scriptsDir + "/" + scriptName;
	if (!QFile::exists(scriptPath))
	{
		ccLog::Error(QString("Script not found: %1").arg(scriptPath));
		return QString();
	}

	QString pythonExe = resolvePythonExe();
	if (pythonExe.isEmpty())
	{
		return QString();
	}

	QStringList fullArgs;
	fullArgs << scriptPath << args;

	QProcess process;
	process.start(pythonExe, fullArgs);
	if (!process.waitForStarted(5000))
	{
		ccLog::Error(QString("Failed to start Python interpreter: %1").arg(pythonExe));
		return QString();
	}
	if (!process.waitForFinished(120000)) // 2 minute timeout (KNN on big clouds can be slow)
	{
		process.kill();
		process.waitForFinished(3000);
		ccLog::Error(QString("Python script timed out: %1").arg(scriptName));
		return QString();
	}

	if (process.exitCode() != 0)
	{
		// the scripts print {"error": ...} to stdout and details to stderr
		QString err = QString::fromUtf8(process.readAllStandardError()).trimmed();
		QString out = QString::fromUtf8(process.readAllStandardOutput()).trimmed();
		ccLog::Error(QString("Python script '%1' failed: %2").arg(scriptName, err.isEmpty() ? out : err));
		return QString();
	}

	return QString::fromUtf8(process.readAllStandardOutput());
}

bool ccViewer::exportSelectedCloudToCSV(QTemporaryFile& tempFile)
{
	if (!m_selectedObject) return false;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) return false;

	if (!tempFile.open())
	{
		ccLog::Error("Failed to create temporary file");
		return false;
	}

	QTextStream stream(&tempFile);
	// keep enough digits for global (e.g. UTM) coordinates
	stream.setRealNumberNotation(QTextStream::SmartNotation);
	stream.setRealNumberPrecision(10);
	unsigned n = cloud->size();
	for (unsigned i = 0; i < n; ++i)
	{
		const CCVector3* P = cloud->getPoint(i);
		stream << P->x << "," << P->y << "," << P->z << "\n";
	}
	stream.flush();
	tempFile.flush();

	return true;
}

// ============================================================================
// SLIM: Tools menu - TLS Plane Fitting
// ============================================================================

void ccViewer::doActionTLSPlane()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Export cloud to temp CSV
	QTemporaryFile tempFile(QDir::tempPath() + "/cc_tls_input_XXXXXX.csv");
	if (!exportSelectedCloudToCSV(tempFile))
	{
		ccLog::Error("Failed to export point cloud");
		return;
	}

	// Run Python script
	QString output = runPythonScript("tls_plane.py", QStringList() << tempFile.fileName());
	if (output.isEmpty())
	{
		ccLog::Error("TLS Plane Fitting failed");
		return;
	}

	// Parse JSON result
	QJsonDocument doc = QJsonDocument::fromJson(output.toUtf8());
	if (!doc.isObject())
	{
		ccLog::Error(QString("Failed to parse Python output: %1").arg(output.left(200)));
		return;
	}

	QJsonObject obj = doc.object();
	if (obj.contains("error"))
	{
		ccLog::Error(QString("TLS Plane Fitting failed: %1").arg(obj["error"].toString()));
		return;
	}

	double a = obj["a"].toDouble();
	double b = obj["b"].toDouble();
	double c = obj["c"].toDouble();
	double d = obj["d"].toDouble();
	QString eqn = obj["equation"].toString();
	int npts = obj["num_points"].toInt();

	// Show result in a dialog
	QString msg = QString(
		"<h3>TLS Plane Fitting Result</h3>"
		"<p><b>Plane equation:</b> %1</p>"
		"<p><b>Parameters:</b></p>"
		"<table>"
		"<tr><td>a =</td><td>%2</td></tr>"
		"<tr><td>b =</td><td>%3</td></tr>"
		"<tr><td>c =</td><td>%4</td></tr>"
		"<tr><td>d =</td><td>%5</td></tr>"
		"</table>"
		"<p><b>Normal vector:</b> (%2, %3, %4)</p>"
		"<p><b>Point count:</b> %6</p>"
	).arg(eqn).arg(a, 0, 'f', 6).arg(b, 0, 'f', 6).arg(c, 0, 'f', 6).arg(d, 0, 'f', 6).arg(npts);

	QMessageBox::information(this, tr("TLS Plane Fitting"), msg);
}

// ============================================================================
// SLIM: Tools menu - Point-to-Plane Projection
// ============================================================================

void ccViewer::doActionPointProjection()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Input dialog for plane parameters
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Point to Plane Projection"));
	dlg.setMinimumWidth(400);

	QFormLayout* form = new QFormLayout(&dlg);

	QDoubleSpinBox* spinA = new QDoubleSpinBox(&dlg);
	spinA->setRange(-1000.0, 1000.0);
	spinA->setDecimals(6);
	spinA->setValue(0.0);
	form->addRow(tr("A:"), spinA);

	QDoubleSpinBox* spinB = new QDoubleSpinBox(&dlg);
	spinB->setRange(-1000.0, 1000.0);
	spinB->setDecimals(6);
	spinB->setValue(0.0);
	form->addRow(tr("B:"), spinB);

	QDoubleSpinBox* spinC = new QDoubleSpinBox(&dlg);
	spinC->setRange(-1000.0, 1000.0);
	spinC->setDecimals(6);
	spinC->setValue(1.0);
	form->addRow(tr("C:"), spinC);

	QDoubleSpinBox* spinD = new QDoubleSpinBox(&dlg);
	spinD->setRange(-100000.0, 100000.0);
	spinD->setDecimals(6);
	spinD->setValue(0.0);
	form->addRow(tr("D:"), spinD);

	QCheckBox* chkCreateCloud = new QCheckBox(tr("Create projected point cloud in 3D view"), &dlg);
	chkCreateCloud->setChecked(true);
	form->addRow(chkCreateCloud);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	form->addRow(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	double A = spinA->value();
	double B = spinB->value();
	double C = spinC->value();
	double D = spinD->value();
	if (A == 0.0 && B == 0.0 && C == 0.0)
	{
		ccLog::Error("Invalid plane: the normal (A, B, C) cannot be zero");
		return;
	}
	bool createCloud = chkCreateCloud->isChecked();

	// Export cloud to temp CSV
	QTemporaryFile tempFile(QDir::tempPath() + "/cc_projection_input_XXXXXX.csv");
	if (!exportSelectedCloudToCSV(tempFile))
	{
		ccLog::Error("Failed to export point cloud");
		return;
	}

	// Create temp output file for projected points
	QTemporaryFile tempOutFile(QDir::tempPath() + "/cc_projection_output_XXXXXX.csv");
	if (!tempOutFile.open())
	{
		ccLog::Error("Failed to create temporary output file");
		return;
	}
	QString outPath = tempOutFile.fileName();
	tempOutFile.close(); // keep the file on disk (deleted with the QTemporaryFile object)

	// Run Python script: point_projection.py <input_csv> <A> <B> <C> <D> [output_csv]
	QString output = runPythonScript("point_projection.py",
		QStringList() << tempFile.fileName()
		<< QString::number(A) << QString::number(B)
		<< QString::number(C) << QString::number(D)
		<< outPath);

	if (output.isEmpty())
	{
		ccLog::Error("Point Projection failed");
		return;
	}

	// Read projected points from output CSV
	ccPointCloud* projectedCloud = nullptr;
	if (createCloud && QFile::exists(outPath))
	{
		projectedCloud = new ccPointCloud(cloud->getName() + QString(".projected"));
		if (!projectedCloud->reserve(cloud->size()))
		{
			delete projectedCloud;
			projectedCloud = nullptr;
		}
		else
		{
			// Read CSV
			QFile outFile(outPath);
			if (outFile.open(QIODevice::ReadOnly | QIODevice::Text))
			{
				QTextStream in(&outFile);
				// Skip header
				if (!in.atEnd()) in.readLine();
				while (!in.atEnd())
				{
					QString line = in.readLine().trimmed();
					if (line.isEmpty()) continue;
					QStringList parts = line.split(",");
					if (parts.size() >= 3)
					{
						CCVector3 P(
							static_cast<PointCoordinateType>(parts[0].toDouble()),
							static_cast<PointCoordinateType>(parts[1].toDouble()),
							static_cast<PointCoordinateType>(parts[2].toDouble())
						);
						projectedCloud->addPoint(P);
					}
				}
				outFile.close();
			}
		}

		if (projectedCloud && projectedCloud->size() > 0)
		{
			// Copy colors from original
			if (cloud->hasColors() && projectedCloud->reserveTheRGBTable())
			{
				for (unsigned i = 0; i < projectedCloud->size() && i < cloud->size(); ++i)
				{
					projectedCloud->addColor(cloud->getPointColor(i));
				}
				projectedCloud->showColors(true);
			}
			addToDB(projectedCloud, true, true, false, true);
		}
		else if (projectedCloud)
		{
			delete projectedCloud;
			projectedCloud = nullptr;
		}
	}

	// Show summary
	QString planeEqn = QString("%1x + %2y + %3z + %4 = 0").arg(A).arg(B).arg(C).arg(D);
	QString msg = QString(
		"<h3>Point-to-Plane Projection Result</h3>"
		"<p><b>Plane:</b> %1</p>"
		"<p><b>Points projected:</b> %2</p>"
		"%3"
	).arg(planeEqn).arg(cloud->size())
	 .arg(createCloud && projectedCloud && projectedCloud->size() > 0 ?
		  QString("<p>Projected point cloud added to 3D view.</p>") :
		  QString("<p>Projected results saved to: %1</p>").arg(outPath));

	QMessageBox::information(this, tr("Point to Plane Projection"), msg);
}

// ============================================================================
// SLIM: Tools menu - KNN Search
// ============================================================================

void ccViewer::doActionKNNSearch()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Input dialog for K
	bool ok = false;
	int K = QInputDialog::getInt(this, tr("KNN Search"),
		tr("Number of nearest neighbors (K):"), 5, 1,
		static_cast<int>(std::min<unsigned>(cloud->size(), 100)), 1, &ok);
	if (!ok) return;

	// Export cloud to temp CSV
	QTemporaryFile tempFile(QDir::tempPath() + "/cc_knn_input_XXXXXX.csv");
	if (!exportSelectedCloudToCSV(tempFile))
	{
		ccLog::Error("Failed to export point cloud");
		return;
	}

	// Run Python script: knn_search.py <input_csv> <K>
	QString output = runPythonScript("knn_search.py",
		QStringList() << tempFile.fileName() << QString::number(K));
	if (output.isEmpty())
	{
		ccLog::Error("KNN Search failed");
		return;
	}

	// Parse JSON result
	QJsonDocument doc = QJsonDocument::fromJson(output.toUtf8());
	if (!doc.isObject())
	{
		ccLog::Error(QString("Failed to parse Python output: %1").arg(output.left(200)));
		return;
	}

	QJsonObject obj = doc.object();
	if (obj.contains("error"))
	{
		ccLog::Error(QString("KNN Search failed: %1").arg(obj["error"].toString()));
		return;
	}

	int numPoints = obj["num_points"].toInt();
	int kVal = obj["K"].toInt();
	QJsonObject summary = obj["summary"].toObject();
	double meanDist = summary["mean_nearest_distance"].toDouble();
	double maxDist = summary["max_nearest_distance"].toDouble();

	QString msg = QString(
		"<h3>KNN Search Result</h3>"
		"<p><b>Points:</b> %1</p>"
		"<p><b>K:</b> %2</p>"
		"<p><b>Mean nearest-neighbor distance:</b> %3</p>"
		"<p><b>Max nearest-neighbor distance:</b> %4</p>"
	).arg(numPoints).arg(kVal).arg(meanDist, 0, 'f', 6).arg(maxDist, 0, 'f', 6);

	QMessageBox::information(this, tr("KNN Search"), msg);
}

// ============================================================================
// SLIM: Tools menu - Rotation Matrix
// ============================================================================

void ccViewer::doActionRotationMatrix()
{
	// Input dialog for two normal vectors
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Rotation Matrix Calculator"));
	dlg.setMinimumWidth(450);

	QVBoxLayout* mainLayout = new QVBoxLayout(&dlg);

	// Normal 1
	QLabel* label1 = new QLabel(tr("<b>Normal Vector 1 (source):</b>"), &dlg);
	mainLayout->addWidget(label1);
	QFormLayout* form1 = new QFormLayout();

	QDoubleSpinBox* x1 = new QDoubleSpinBox(&dlg);
	x1->setRange(-1000.0, 1000.0);
	x1->setDecimals(6);
	x1->setValue(0.0);
	form1->addRow(tr("X1:"), x1);

	QDoubleSpinBox* y1 = new QDoubleSpinBox(&dlg);
	y1->setRange(-1000.0, 1000.0);
	y1->setDecimals(6);
	y1->setValue(0.0);
	form1->addRow(tr("Y1:"), y1);

	QDoubleSpinBox* z1 = new QDoubleSpinBox(&dlg);
	z1->setRange(-1000.0, 1000.0);
	z1->setDecimals(6);
	z1->setValue(1.0);
	form1->addRow(tr("Z1:"), z1);

	mainLayout->addLayout(form1);

	// Normal 2
	QLabel* label2 = new QLabel(tr("<b>Normal Vector 2 (target):</b>"), &dlg);
	mainLayout->addWidget(label2);
	QFormLayout* form2 = new QFormLayout();

	QDoubleSpinBox* x2 = new QDoubleSpinBox(&dlg);
	x2->setRange(-1000.0, 1000.0);
	x2->setDecimals(6);
	x2->setValue(1.0);
	form2->addRow(tr("X2:"), x2);

	QDoubleSpinBox* y2 = new QDoubleSpinBox(&dlg);
	y2->setRange(-1000.0, 1000.0);
	y2->setDecimals(6);
	y2->setValue(0.0);
	form2->addRow(tr("Y2:"), y2);

	QDoubleSpinBox* z2 = new QDoubleSpinBox(&dlg);
	z2->setRange(-1000.0, 1000.0);
	z2->setDecimals(6);
	z2->setValue(0.0);
	form2->addRow(tr("Z2:"), z2);

	mainLayout->addLayout(form2);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	mainLayout->addWidget(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	double nx1 = x1->value(), ny1 = y1->value(), nz1 = z1->value();
	double nx2 = x2->value(), ny2 = y2->value(), nz2 = z2->value();

	// Validate: vectors should not be zero
	if (nx1 == 0.0 && ny1 == 0.0 && nz1 == 0.0)
	{
		ccLog::Error("Normal vector 1 cannot be zero");
		return;
	}
	if (nx2 == 0.0 && ny2 == 0.0 && nz2 == 0.0)
	{
		ccLog::Error("Normal vector 2 cannot be zero");
		return;
	}

	// Run Python script: rotation_matrix.py <x1> <y1> <z1> <x2> <y2> <z2>
	QString output = runPythonScript("rotation_matrix.py",
		QStringList() << QString::number(nx1) << QString::number(ny1) << QString::number(nz1)
		<< QString::number(nx2) << QString::number(ny2) << QString::number(nz2));
	if (output.isEmpty())
	{
		ccLog::Error("Rotation Matrix computation failed");
		return;
	}

	// Parse JSON result
	QJsonDocument doc = QJsonDocument::fromJson(output.toUtf8());
	if (!doc.isObject())
	{
		ccLog::Error(QString("Failed to parse Python output: %1").arg(output.left(200)));
		return;
	}

	QJsonObject obj = doc.object();
	if (obj.contains("error"))
	{
		ccLog::Error(QString("Rotation Matrix computation failed: %1").arg(obj["error"].toString()));
		return;
	}

	QJsonArray R = obj["rotation_matrix"].toArray();
	double error = obj["verification_error"].toDouble();

	// Format the matrix
	QString matrixStr;
	for (int row = 0; row < 3; ++row)
	{
		QJsonArray rowArr = R[row].toArray();
		matrixStr += QString("| %1  %2  %3 |\n")
			.arg(rowArr[0].toDouble(), 10, 'f', 6)
			.arg(rowArr[1].toDouble(), 10, 'f', 6)
			.arg(rowArr[2].toDouble(), 10, 'f', 6);
	}

	QString msg = QString(
		"<h3>Rotation Matrix Result</h3>"
		"<p><b>Source normal (v1):</b> (%1, %2, %3)</p>"
		"<p><b>Target normal (v2):</b> (%4, %5, %6)</p>"
		"<p><b>Rotation Matrix (3x3):</b></p>"
		"<pre>%7</pre>"
		"<p><b>Verification:</b> ||R*v1 - v2|| = %8</p>"
	).arg(nx1).arg(ny1).arg(nz1)
	 .arg(nx2).arg(ny2).arg(nz2)
	 .arg(matrixStr)
	 .arg(error, 0, 'e', 6);

	QMessageBox::information(this, tr("Rotation Matrix"), msg);
}



// ============================================================================
// SLIM: Tools menu - Boundary Point Extract (Native C++)
// ============================================================================

void ccViewer::doActionBoundaryExtract()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Parameter dialog
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Boundary Point Extract"));
	dlg.setMinimumWidth(400);

	QFormLayout* form = new QFormLayout(&dlg);

	QSpinBox* spinK = new QSpinBox(&dlg);
	spinK->setRange(5, 500);
	spinK->setValue(30);
	spinK->setToolTip(tr("Number of nearest neighbors for local plane fitting"));
	form->addRow(tr("K (neighbors):"), spinK);

	QDoubleSpinBox* spinAngle = new QDoubleSpinBox(&dlg);
	spinAngle->setRange(0.0, 180.0);
	spinAngle->setDecimals(1);
	spinAngle->setValue(120.0);
	spinAngle->setSuffix(tr(" deg"));
	spinAngle->setToolTip(tr("Angular gap threshold. Points with a larger max gap are classified as boundary."));
	form->addRow(tr("Angle threshold:"), spinAngle);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	form->addRow(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	int K = spinK->value();
	double angleThreshold = spinAngle->value();

	// Run algorithm
	ccPointCloud* result = boundaryExtract(cloud, K, angleThreshold);
	if (!result)
	{
		ccLog::Error("Boundary extract failed or no boundary points found");
		return;
	}

	addToDB(result, true, true, false, true);
	ccLog::Print(QString("[Boundary Extract] Found %1 boundary points").arg(result->size()));

	QString msg = QString(
		"<h3>Boundary Point Extract Result</h3>"
		"<p><b>Input points:</b> %1</p>"
		"<p><b>Boundary points found:</b> %2</p>"
		"<p><b>K:</b> %3 | <b>Angle threshold:</b> %4 deg</p>"
		"<p>Boundary point cloud added to 3D view.</p>"
	).arg(cloud->size()).arg(result->size()).arg(K).arg(angleThreshold, 0, 'f', 1);

	QMessageBox::information(this, tr("Boundary Point Extract"), msg);
}

// ============================================================================
// SLIM: Tools menu - Fold Point Extract (Native C++)
// ============================================================================

void ccViewer::doActionFoldExtract()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Compute a reasonable default radius (1% of bounding-box diagonal)
	ccBBox bbox = cloud->getOwnBB();
	CCVector3 diag = bbox.maxCorner() - bbox.minCorner();
	double autoRadius = std::sqrt(static_cast<double>(diag.x)*diag.x +
	                              static_cast<double>(diag.y)*diag.y +
	                              static_cast<double>(diag.z)*diag.z) * 0.01;
	if (autoRadius < 1e-6) autoRadius = 0.1;

	// Parameter dialog
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Fold Point Extract"));
	dlg.setMinimumWidth(450);

	QFormLayout* form = new QFormLayout(&dlg);

	QDoubleSpinBox* spinRadius = new QDoubleSpinBox(&dlg);
	spinRadius->setRange(0.0001, 10000.0);
	spinRadius->setDecimals(6);
	spinRadius->setValue(autoRadius);
	spinRadius->setToolTip(tr("Sphere neighborhood radius (approx. 10x point spacing)"));
	form->addRow(tr("Radius:"), spinRadius);

	QDoubleSpinBox* spinPL = new QDoubleSpinBox(&dlg);
	spinPL->setRange(0.0, 1000.0);
	spinPL->setDecimals(6);
	spinPL->setValue(0.005);
	spinPL->setToolTip(tr("Std-dev threshold for point-to-line distances"));
	form->addRow(tr("PL threshold:"), spinPL);

	QDoubleSpinBox* spinDPDS = new QDoubleSpinBox(&dlg);
	spinDPDS->setRange(1.0, 100.0);
	spinDPDS->setDecimals(1);
	spinDPDS->setValue(4.0);
	spinDPDS->setToolTip(tr("Side imbalance ratio threshold (left/right)"));
	form->addRow(tr("DP_DS:"), spinDPDS);

	QSpinBox* spinRank = new QSpinBox(&dlg);
	spinRank->setRange(1, 100);
	spinRank->setValue(3);
	spinRank->setToolTip(tr("Rank threshold for farthest-from-line selection"));
	form->addRow(tr("Rank threshold:"), spinRank);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	form->addRow(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	double radius = spinRadius->value();
	double PL_threshold = spinPL->value();
	double DP_DS = spinDPDS->value();
	int rank_dis_threshold = spinRank->value();

	// Run algorithm
	ccPointCloud* result = foldExtract(cloud, radius, PL_threshold, DP_DS, rank_dis_threshold);
	if (!result)
	{
		ccLog::Error("Fold extract failed or no fold points found");
		return;
	}

	addToDB(result, true, true, false, true);
	ccLog::Print(QString("[Fold Extract] Found %1 fold points").arg(result->size()));

	QString msg = QString(
		"<h3>Fold Point Extract Result</h3>"
		"<p><b>Input points:</b> %1</p>"
		"<p><b>Fold points found:</b> %2</p>"
		"<p><b>Parameters:</b> radius=%3, PL_th=%4, DP_DS=%5, rank=%6</p>"
		"<p>Fold point cloud added to 3D view.</p>"
	).arg(cloud->size()).arg(result->size())
	 .arg(radius, 0, 'f', 4).arg(PL_threshold, 0, 'f', 6)
	 .arg(DP_DS, 0, 'f', 1).arg(rank_dis_threshold);

	QMessageBox::information(this, tr("Fold Point Extract"), msg);
}

// ============================================================================
// SLIM: Tools menu - Sphere Neighborhood (Native C++)
// ============================================================================

void ccViewer::doActionSphereNeighborhood()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Compute default radius
	ccBBox bbox = cloud->getOwnBB();
	CCVector3 diag = bbox.maxCorner() - bbox.minCorner();
	double autoRadius = std::sqrt(static_cast<double>(diag.x)*diag.x +
	                              static_cast<double>(diag.y)*diag.y +
	                              static_cast<double>(diag.z)*diag.z) * 0.02;
	if (autoRadius < 1e-6) autoRadius = 0.1;

	// Parameter dialog
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Sphere Neighborhood"));
	dlg.setMinimumWidth(400);

	QFormLayout* form = new QFormLayout(&dlg);

	QDoubleSpinBox* spinRadius = new QDoubleSpinBox(&dlg);
	spinRadius->setRange(0.0001, 10000.0);
	spinRadius->setDecimals(6);
	spinRadius->setValue(autoRadius);
	spinRadius->setToolTip(tr("Search radius for spherical neighborhood"));
	form->addRow(tr("Radius:"), spinRadius);

	QCheckBox* chkAll = new QCheckBox(tr("Compute statistics for all points"), &dlg);
	chkAll->setChecked(false);
	form->addRow(chkAll);

	QSpinBox* spinIdx = new QSpinBox(&dlg);
	spinIdx->setRange(0, static_cast<int>(cloud->size()) - 1);
	spinIdx->setValue(0);
	spinIdx->setToolTip(tr("Index of the query point"));
	form->addRow(tr("Query point index:"), spinIdx);

	// Toggle query index based on "all points" checkbox
	QObject::connect(chkAll, &QCheckBox::toggled, spinIdx, &QSpinBox::setDisabled);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	form->addRow(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	double radius = spinRadius->value();
	bool allPoints = chkAll->isChecked();
	int queryIdx = allPoints ? -1 : spinIdx->value();

	unsigned count = 0;
	double avgDist = 0.0, minDist = 0.0, maxDist = 0.0;

	ccPointCloud* result = sphereNeighborhoodExtract(cloud, radius, queryIdx,
	                                                  count, avgDist, minDist, maxDist);

	if (result)
	{
		// Single-point result
		addToDB(result, true, true, false, true);
		ccLog::Print(QString("[Sphere Neighborhood] %1 neighbors for point %2")
		             .arg(count).arg(queryIdx));

		QString msg = QString(
			"<h3>Sphere Neighborhood Result</h3>"
			"<p><b>Query point:</b> %1</p>"
			"<p><b>Radius:</b> %2</p>"
			"<p><b>Neighbors found:</b> %3</p>"
			"<p><b>Avg distance:</b> %4 | <b>Min:</b> %5 | <b>Max:</b> %6</p>"
			"<p>Neighborhood cloud added to 3D view.</p>"
		).arg(queryIdx).arg(radius, 0, 'f', 6).arg(count)
		 .arg(avgDist, 0, 'f', 6).arg(minDist, 0, 'f', 6).arg(maxDist, 0, 'f', 6);

		QMessageBox::information(this, tr("Sphere Neighborhood"), msg);
	}
	else if (allPoints)
	{
		// All-points statistics (no cloud)
		QString msg = QString(
			"<h3>Sphere Neighborhood Statistics (All Points)</h3>"
			"<p><b>Total points:</b> %1</p>"
			"<p><b>Radius:</b> %2</p>"
			"<p><b>Average neighbors per point:</b> %3</p>"
			"<p><b>Min neighbors:</b> %4 | <b>Max neighbors:</b> %5</p>"
		).arg(cloud->size()).arg(radius, 0, 'f', 6)
		 .arg(avgDist, 0, 'f', 2).arg(static_cast<int>(minDist)).arg(static_cast<int>(maxDist));

		QMessageBox::information(this, tr("Sphere Neighborhood"), msg);
	}
	else
	{
		ccLog::Error("No neighbors found for the specified query point");
	}
}

// ============================================================================
// SLIM: Tools menu - Sphere PCA (Native C++)
// ============================================================================

void ccViewer::doActionSpherePCA()
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud) { ccLog::Error("Select a point cloud first"); return; }

	// Compute default radius
	ccBBox bbox = cloud->getOwnBB();
	CCVector3 diag = bbox.maxCorner() - bbox.minCorner();
	double autoRadius = std::sqrt(static_cast<double>(diag.x)*diag.x +
	                              static_cast<double>(diag.y)*diag.y +
	                              static_cast<double>(diag.z)*diag.z) * 0.02;
	if (autoRadius < 1e-6) autoRadius = 0.1;

	// Parameter dialog
	QDialog dlg(this);
	dlg.setWindowTitle(tr("Sphere PCA"));
	dlg.setMinimumWidth(400);

	QFormLayout* form = new QFormLayout(&dlg);

	QDoubleSpinBox* spinRadius = new QDoubleSpinBox(&dlg);
	spinRadius->setRange(0.0001, 10000.0);
	spinRadius->setDecimals(6);
	spinRadius->setValue(autoRadius);
	spinRadius->setToolTip(tr("Sphere neighborhood radius for local PCA"));
	form->addRow(tr("Radius:"), spinRadius);

	QDialogButtonBox* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dlg);
	connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
	connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);
	form->addRow(buttons);

	if (dlg.exec() != QDialog::Accepted)
		return;

	double radius = spinRadius->value();

	// Run algorithm
	if (!spherePCACompute(cloud, radius))
	{
		ccLog::Error("Sphere PCA computation failed");
		return;
	}

	m_glWindow->redraw();
	ccLog::Print(QString("[Sphere PCA] Normals computed for %1 points (radius=%2)")
	             .arg(cloud->size()).arg(radius, 0, 'f', 6));

	QString msg = QString(
		"<h3>Sphere PCA Result</h3>"
		"<p><b>Points processed:</b> %1</p>"
		"<p><b>Radius:</b> %2</p>"
		"<p>PCA max-eigenvector normals stored as scalar fields:</p>"
		"<ul><li>PCA_normal_x</li><li>PCA_normal_y</li><li>PCA_normal_z</li></ul>"
		"<p>Use <b>Edit &gt; Scalar Fields</b> to visualize them.</p>"
	).arg(cloud->size()).arg(radius, 0, 'f', 6);

	QMessageBox::information(this, tr("Sphere PCA"), msg);
}
// ============================================================================
// SLIM: ccMainAppInterface - fixed implementations
// ============================================================================

const ccHObject::Container& ccViewer::getSelectedEntities() const
{
	m_selectedEntities.clear();
	if (m_selectedObject) m_selectedEntities.push_back(m_selectedObject);
	return m_selectedEntities;
}

void ccViewer::setSelectedInDB(ccHObject* obj, bool selected)
{
	if (obj && m_glWindow)
	{
		obj->setSelected(selected);
		if (selected) m_selectedObject = obj;
		else if (m_selectedObject == obj) m_selectedObject = nullptr;
	}
}

void ccViewer::updateUI()
{
	if (m_glWindow)
	{
		reflectPerspectiveState();
		reflectPivotVisibilityState();
		reflectLightsState();
	}
}

void ccViewer::dispToConsole(QString message, ConsoleMessageLevel level)
{
	printf("%s\n", qUtf8Printable(message));

	// Also write to log file
	if (auto* log = ccViewerLog::instance())
	{
		int logLevel;
		switch (level)
		{
		case ERR_CONSOLE_MESSAGE:
			logLevel = ccLog::LOG_ERROR;
			break;
		case WRN_CONSOLE_MESSAGE:
			logLevel = ccLog::LOG_WARNING;
			break;
		default:
			logLevel = ccLog::LOG_STANDARD;
			break;
		}
		log->writeToFile(message, logLevel);
	}

	if (level == ERR_CONSOLE_MESSAGE)
	{
		QMessageBox::warning(this, tr("Error"), message);
	}
	else if (level == WRN_CONSOLE_MESSAGE)
	{
		statusBar()->showMessage(message, 8000);
	}
}

ccHObject* ccViewer::dbRootObject() { return m_glWindow->getSceneDB(); }
void ccViewer::redrawAll(bool only2D) { m_glWindow->redraw(only2D); }
void ccViewer::refreshAll(bool only2D) { m_glWindow->refresh(only2D); }
void ccViewer::enableAll() { m_glWindow->asWidget()->setEnabled(true); }
void ccViewer::disableAll() { m_glWindow->asWidget()->setEnabled(false); }
void ccViewer::disableAllBut(ccGLWindowInterface* win) { if (win != m_glWindow) m_glWindow->asWidget()->setEnabled(false); }
void ccViewer::setView(CC_VIEW_ORIENTATION view) { m_glWindow->setView(view, true); }
void ccViewer::toggleActiveWindowCustomLight() { ui.actionToggleCustomLight->setChecked(!ui.actionToggleCustomLight->isChecked()); }
void ccViewer::toggleActiveWindowSunLight() { ui.actionToggleSunLight->setChecked(!ui.actionToggleSunLight->isChecked()); }

void ccViewer::toggleActiveWindowCenteredPerspective()
{
	if (ui.actionSetCenteredPerspectiveView->isChecked()) ui.actionSetOrthoView->trigger();
	else ui.actionSetCenteredPerspectiveView->trigger();
}

void ccViewer::toggleActiveWindowViewerBasedPerspective()
{
	if (ui.actionSetViewerPerspectiveView->isChecked()) ui.actionSetOrthoView->trigger();
	else ui.actionSetViewerPerspectiveView->trigger();
}

void ccViewer::increasePointSize() { m_glWindow->setPointSize(m_glWindow->getViewportParameters().defaultPointSize + 1); m_glWindow->redraw(); }
void ccViewer::decreasePointSize() { m_glWindow->setPointSize(m_glWindow->getViewportParameters().defaultPointSize - 1); m_glWindow->redraw(); }
ccUniqueIDGenerator::Shared ccViewer::getUniqueIDGenerator() { return ccObject::GetUniqueIDGenerator(); }

static QAction* FindAction(const QList<QAction*>& actions, const QString& name)
{
	for (QAction* action : actions)
		if (action->text() == name) return action;
	return nullptr;
}

void ccViewer::selectNextSF(int deltaPos)
{
	if (!m_selectedObject) return;
	ccPointCloud* cloud = ccHObjectCaster::ToPointCloud(m_selectedObject);
	if (!cloud || !cloud->hasScalarFields()) return;
	int sfIdx = cloud->getCurrentDisplayedScalarFieldIndex();
	int newSFIndex = std::max(0, std::min(static_cast<int>(cloud->getNumberOfScalarFields()) - 1, sfIdx + deltaPos));
	if (newSFIndex != sfIdx)
	{
		QAction* newAction = FindAction(ui.menuSelectSF->actions(), QString::fromStdString(cloud->getScalarFieldName(newSFIndex)));
		if (newAction) newAction->setChecked(true);
	}
}

// ============================================================================
// 3D Mouse support
// ============================================================================

void ccViewer::release3DMouse()
{
#ifdef CC_3DXWARE_SUPPORT
	if (m_3dMouseInput) { m_3dMouseInput->disconnect(); disconnect(m_3dMouseInput); delete m_3dMouseInput; m_3dMouseInput = 0; }
#endif
}

void ccViewer::enable3DMouse(bool state)
{
#ifdef CC_3DXWARE_SUPPORT
	if (m_3dMouseInput) release3DMouse();
	if (state)
	{
		m_3dMouseInput = new Mouse3DInput(this);
		if (m_3dMouseInput->connect(this, "ccViewer"))
		{
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigMove3d, this, &ccViewer::on3DMouseMove);
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigReleased, this, &ccViewer::on3DMouseReleased);
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigOn3dmouseKeyDown, this, &ccViewer::on3DMouseKeyDown);
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigOn3dmouseKeyUp, this, &ccViewer::on3DMouseKeyUp);
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigOn3dmouseCMDKeyDown, this, &ccViewer::on3DMouseCMDKeyDown);
			QObject::connect(m_3dMouseInput, &Mouse3DInput::sigOn3dmouseCMDKeyUp, this, &ccViewer::on3DMouseCMDKeyUp);
		}
		else { delete m_3dMouseInput; m_3dMouseInput = 0; ccLog::Warning("[3D Mouse] No device found"); state = false; }
	}
	else ccLog::Warning("[3D Mouse] Device has been disabled");
#else
	state = false;
#endif
	ui.actionEnable3DMouse->blockSignals(true);
	ui.actionEnable3DMouse->setChecked(state);
	ui.actionEnable3DMouse->blockSignals(false);
}

void ccViewer::on3DMouseKeyUp(int) {}
void ccViewer::on3DMouseCMDKeyUp(int) {}

void ccViewer::on3DMouseKeyDown(int key)
{
#ifdef CC_3DXWARE_SUPPORT
	switch (key)
	{
	case Mouse3DInput::V3DK_FIT: if (m_selectedObject) zoomOnSelectedEntity(); else setGlobalZoom(); break;
	case Mouse3DInput::V3DK_TOP: setTopView(); break;
	case Mouse3DInput::V3DK_LEFT: setLeftView(); break;
	case Mouse3DInput::V3DK_RIGHT: setRightView(); break;
	case Mouse3DInput::V3DK_FRONT: setFrontView(); break;
	case Mouse3DInput::V3DK_BOTTOM: setBottomView(); break;
	case Mouse3DInput::V3DK_BACK: setBackView(); break;
	case Mouse3DInput::V3DK_ISO1: setIsoView1(); break;
	case Mouse3DInput::V3DK_ISO2: setIsoView2(); break;
	default: break;
	}
#endif
}

void ccViewer::on3DMouseCMDKeyDown(int cmd)
{
#ifdef CC_3DXWARE_SUPPORT
	switch (cmd)
	{
	case Mouse3DInput::V3DCMD_VIEW_FIT: if (m_selectedObject) zoomOnSelectedEntity(); else setGlobalZoom(); break;
	case Mouse3DInput::V3DCMD_VIEW_TOP: setTopView(); break;
	case Mouse3DInput::V3DCMD_VIEW_LEFT: setLeftView(); break;
	case Mouse3DInput::V3DCMD_VIEW_RIGHT: setRightView(); break;
	case Mouse3DInput::V3DCMD_VIEW_FRONT: setFrontView(); break;
	case Mouse3DInput::V3DCMD_VIEW_BOTTOM: setBottomView(); break;
	case Mouse3DInput::V3DCMD_VIEW_BACK: setBackView(); break;
	case Mouse3DInput::V3DCMD_VIEW_ISO1: setIsoView1(); break;
	case Mouse3DInput::V3DCMD_VIEW_ISO2: setIsoView2(); break;
	default: break;
	}
#endif
}

void ccViewer::on3DMouseMove(std::vector<float>& vec)
{
#ifdef CC_3DXWARE_SUPPORT
	if (m_glWindow) Mouse3DInput::Apply(vec, m_glWindow);
#endif
}

void ccViewer::on3DMouseReleased()
{
	if (m_glWindow && m_glWindow->getPivotVisibility() == ccGLWindowInterface::PIVOT_SHOW_ON_MOVE)
	{ m_glWindow->showPivotSymbol(false); m_glWindow->redraw(); }
}
