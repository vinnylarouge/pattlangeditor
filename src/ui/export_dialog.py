from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem, QDialogButtonBox, QLabel, QHeaderView, QComboBox
from PySide6.QtCore import Qt

class ExportDialog(QDialog):
    def __init__(self, signature, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export to PyTorch / Colab")
        self.resize(800, 600)
        self.signature = signature
        
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: General (Hyperparameters)
        self.general_tab = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Tab 2: Wires (Dimensions)
        self.wires_tab = QWidget()
        self.setup_wires_tab()
        self.tabs.addTab(self.wires_tab, "Wire Dimensions")
        
        # Tab 3: Morphisms (Implementation)
        self.morphisms_tab = QWidget()
        self.setup_morphisms_tab()
        self.tabs.addTab(self.morphisms_tab, "Morphism Implementation")
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def setup_general_tab(self):
        layout = QFormLayout(self.general_tab)
        
        self.batch_size = QLineEdit("32")
        self.epochs = QLineEdit("10")
        self.lr = QLineEdit("0.001")
        self.optimizer = QComboBox()
        self.optimizer.addItems(["Adam", "SGD", "RMSprop"])
        
        layout.addRow("Batch Size:", self.batch_size)
        layout.addRow("Epochs:", self.epochs)
        layout.addRow("Learning Rate:", self.lr)
        layout.addRow("Optimizer:", self.optimizer)

    def setup_wires_tab(self):
        layout = QVBoxLayout(self.wires_tab)
        layout.addWidget(QLabel("Specify tensor dimensions for each Wire Type (e.g., '128' or '3, 32, 32')"))
        
        self.wire_table = QTableWidget()
        self.wire_table.setColumnCount(2)
        self.wire_table.setHorizontalHeaderLabels(["Wire Type", "Dimensions"])
        self.wire_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        row = 0
        self.wire_table.setRowCount(len(self.signature.wire_types))
        for name, wt in self.signature.wire_types.items():
            self.wire_table.setItem(row, 0, QTableWidgetItem(name))
            # Default dim suggestion
            dim_item = QTableWidgetItem("128")
            self.wire_table.setItem(row, 1, dim_item)
            row += 1
            
        layout.addWidget(self.wire_table)

    def setup_morphisms_tab(self):
        layout = QVBoxLayout(self.morphisms_tab)
        layout.addWidget(QLabel("Specify PyTorch code for each Morphism (e.g., 'nn.Linear(in_dim, out_dim)')"))
        
        self.morphism_table = QTableWidget()
        self.morphism_table.setColumnCount(2)
        self.morphism_table.setHorizontalHeaderLabels(["Morphism", "PyTorch Code"])
        self.morphism_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        row = 0
        self.morphism_table.setRowCount(len(self.signature.morphisms))
        for name, m in self.signature.morphisms.items():
            self.morphism_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Smart default suggestion
            code = "nn.Identity()"
            if m.type_name == "Learnable":
                code = "nn.Linear(?, ?)" # Placeholder
            elif m.type_name == "Function":
                code = "F.relu"
                
            code_item = QTableWidgetItem(code)
            self.morphism_table.setItem(row, 1, code_item)
            row += 1
            
        layout.addWidget(self.morphism_table)

    def get_data(self):
        # Collect General
        general = {
            "batch_size": self.batch_size.text(),
            "epochs": self.epochs.text(),
            "lr": self.lr.text(),
            "optimizer": self.optimizer.currentText()
        }
        
        # Collect Wires
        wires = {}
        for r in range(self.wire_table.rowCount()):
            name = self.wire_table.item(r, 0).text()
            dim = self.wire_table.item(r, 1).text()
            wires[name] = dim
            
        # Collect Morphisms
        morphisms = {}
        for r in range(self.morphism_table.rowCount()):
            name = self.morphism_table.item(r, 0).text()
            code = self.morphism_table.item(r, 1).text()
            morphisms[name] = code
            
        return {
            "general": general,
            "wires": wires,
            "morphisms": morphisms
        }
